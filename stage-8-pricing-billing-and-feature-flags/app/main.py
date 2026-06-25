"""FastAPI entrypoint — the HTTP face of the Creator Orchestrator.

Run locally:
    uvicorn app.main:app --reload

Endpoints:
    GET  /health          -> liveness probe
    POST /api/orchestrate -> run the full agent pipeline and return artifacts

This route integrates Stage 2 (orchestrator), Stage 3 (memory: session_id/
run_id), and Stage 5 (observability: run_timer). Guardrails and tool RBAC
(Stage 4) still operate inside the agents and tools as previously wired.
"""

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import Artifact, OrchestrateRequest, OrchestrateResponse
from app.orchestrator import build_orchestrator
from app.auth import get_current_principal, router as auth_router
from app.rate_limit import enforce_rate_limit
from billing.quota import enforce_video_quota
from billing.meter import record_usage
from feature_flags.service import is_feature_enabled
from config import AGENT_MODEL
from memory import short_term, episodic
from observability.tracing import run_timer

app = FastAPI(title="Creator Orchestrator API", version="0.8.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth endpoints (POST /auth/token).
app.include_router(auth_router)


def get_orchestrator():
    return build_orchestrator()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(payload: OrchestrateRequest,
                      principal: dict = Depends(get_current_principal),
                      orchestrator=Depends(get_orchestrator)):
    # 0) Identity from the JWT (never trust the request body for identity).
    tenant_id = principal["tenant_id"]
    user_id = principal["user_id"]

    # 1) Rate limit per tenant+user (raises 429 over the limit — velocity).
    enforce_rate_limit(tenant_id, user_id)

    # 2) Plan quota check (raises 402 if no subscription or over quota — volume).
    enforce_video_quota(tenant_id)

    # 3) Feature flags: configure behavior per tenant without redeploying.
    if is_feature_enabled(tenant_id, "use_premium_model"):
        orchestrator.writer_agent.model = "gpt-4o"   # premium tier
    else:
        orchestrator.writer_agent.model = AGENT_MODEL

    # 4) Meter the billable event (one campaign = one VIDEO_INGESTED).
    record_usage(tenant_id, "VIDEO_INGESTED", 1)

    # 5) Open a session + run (short-term + episodic memory), tagged by tenant.
    session_id = short_term.create_session(
        user_id=user_id, topic=payload.topic, tenant_id=tenant_id,
    )
    run_id = episodic.start_run(
        session_id, orchestrator="http-api",
        metadata={"topic": payload.topic}, tenant_id=tenant_id,
    )

    try:
        # 6) Time the run (observability) — the orchestrator does not own the
        #    run because we pass session_id/run_id in.
        with run_timer(run_id, session_id) as rmetrics:
            result = orchestrator.run(
                topic=payload.topic,
                user_id=user_id,
                session_id=session_id,
                run_id=run_id,
                brief=payload.brief,
            )
        episodic.finish_run(run_id, status="success")

        # 3) Map the orchestrator's structured result to API artifacts.
        artifacts = []
        for post in result.get("posts") or []:
            artifacts.append(Artifact(kind="post", content=post))
        if result.get("email"):
            artifacts.append(Artifact(kind="email", content=result["email"]))
        for clip in result.get("clips") or []:
            artifacts.append(Artifact(kind="clip", content=clip))

        return OrchestrateResponse(
            run_id=run_id,
            session_id=session_id,
            artifacts=artifacts,
            metrics={
                "latency_ms": round(rmetrics.latency_ms, 2),
                "token_total": rmetrics.token_total,
                "cost_usd": round(rmetrics.cost_usd, 6),
            },
        )

    except Exception as e:
        episodic.finish_run(run_id, status="error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal error") from e
