# Creator Orchestrator (Stage 6 — Production Repo + HTTP API)

A multi-agent content system that researches a topic, writes a draft, and
reviews it — wrapped in a production-style repository with a FastAPI HTTP API,
Postgres + pgvector for all state, guardrails, evals, and observability.

This is the Stage 6 capstone of a six-stage build:

1. **Stage 1** — Core agent loop + tools
2. **Stage 2** — Orchestrator + specialist agents
3. **Stage 3** — Memory (Postgres + pgvector: short-term, long-term, episodic)
4. **Stage 4** — Guardrails & policy (pre-LLM, post-LLM, tool RBAC)
5. **Stage 5** — Evals & observability (eval harness + metrics)
6. **Stage 6** — Production repo layout + HTTP API (this repo)

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env          # then fill in OPENAI_API_KEY + DATABASE_URL
python -m scripts.migrate     # create tables
python -m scripts.seed        # roles, tool policies, brand policy
uvicorn app.main:app --reload
```

Try it:
```bash
curl localhost:8000/health
curl -X POST localhost:8000/api/orchestrate \
  -H 'content-type: application/json' \
  -d '{"topic":"AI agents for small business","brief":"Audience: SMB owners. Tone: practical.","user_id":"user:marcus"}'
```

Interactive API docs: http://localhost:8000/docs

## Layout

```
app/            FastAPI entrypoint, config (Pydantic settings), API models
agents/         BaseAgent + specialist agents
orchestrator/   code-driven & llm-driven orchestrators
tools/          tool registry + tools (web_search, calculator)
memory/         Postgres + pgvector access (short/long/episodic)
guardrails/     pre-LLM, post-LLM, tool RBAC implementations
security/       named façade over guardrails
evals/          eval harness, rule metrics, LLM-as-a-judge
observability/  run_timer tracing + latency/token/cost metrics
services/       thin façades the API calls (conversation, memory, guardrails, evals)
migrations/     SQL migrations (001 memory, 002 guardrails, 003 evals)
scripts/        migrate / seed / healthcheck
tests/          pytest suite (api, agents, memory, guardrails, orchestrator)
docs/           architecture, api-reference, deployment
infra/          docker-compose, pyproject
```

See [docs/architecture.md](docs/architecture.md), [docs/api-reference.md](docs/api-reference.md),
and [docs/deployment.md](docs/deployment.md).
