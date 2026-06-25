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
from memory import short_term, episodic
from observability.tracing import run_timer

app = FastAPI(title="Creator Orchestrator API", version="0.6.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_orchestrator():
    return build_orchestrator()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(payload: OrchestrateRequest,
                      orchestrator=Depends(get_orchestrator)):
    # 1) Open a session + run (short-term + episodic memory).
    session_id = short_term.create_session(
        user_id=payload.user_id, topic=payload.topic,
    )
    run_id = episodic.start_run(
        session_id, orchestrator="http-api", metadata={"topic": payload.topic},
    )

    try:
        # 2) Time the run (observability) — the orchestrator does not own the
        #    run because we pass session_id/run_id in.
        with run_timer(run_id, session_id) as rmetrics:
            result = orchestrator.run(
                topic=payload.topic,
                user_id=payload.user_id,
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
