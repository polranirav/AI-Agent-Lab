# Architecture

The Creator Orchestrator is a multi-agent content system built in six stages.
Everything runs on **Postgres + pgvector** as the single source of truth.

## Stages

| Stage | Concern | Where it lives |
|-------|---------|----------------|
| 1 | Core agent loop + tools | `agents/`, `tools/` |
| 2 | Orchestrator + specialist agents | `orchestrator/` |
| 3 | Memory (short-term, long-term, episodic) | `memory/` |
| 4 | Guardrails & policy (pre-LLM, post-LLM, tool RBAC) | `guardrails/`, `security/` |
| 5 | Evals & observability | `evals/`, `observability/` |
| 6 | Production repo + HTTP API | `app/`, `services/`, `scripts/`, `infra/` |

## Request flow (HTTP)

```
POST /api/orchestrate
   -> app/main.py            (FastAPI route)
   -> services/conversation  (open session + run)
   -> observability.run_timer (latency / tokens / cost)
   -> orchestrator.run()      research -> write -> review
        -> agents (BaseAgent)  pre-LLM guard -> LLM loop -> post-LLM guard
            -> tools.execute   tool RBAC guard
   -> map result -> artifacts -> OrchestrateResponse
```

## Data model (one trace, keyed by `run_id`)

- `sessions`, `messages` — short-term memory
- `memories` — long-term semantic memory (pgvector)
- `runs`, `events` — episodic memory + observability metrics (in `runs.metadata`)
- `guardrail_policies`, `guardrail_events`, `roles`, `user_roles`, `tool_policies` — guardrails + RBAC
- `eval_results` — evaluation scores

All tables share `run_id`, so runs, events, guardrail events, metrics, and eval
scores can be joined into a single timeline.

## Layers

- **app/** — transport (HTTP), config, request/response models.
- **services/** — thin façades the API uses (conversation, memory, guardrails, evals).
- **security/** — named home for safety policy (wraps Stage 4 guardrails).
- **agents/ + orchestrator/ + tools/** — the reasoning core.
- **memory/ + observability/ + evals/** — data, telemetry, evaluation.
- **scripts/ + infra/ + tests/ + docs/** — operations.
