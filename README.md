# 🧠 AI Agent Lab

> **Build a production-grade, enterprise AI agent platform from scratch — one focused stage at a time.**

This repository is a **learn-by-building journey**: eight self-contained stages
that take a bare LLM call and grow it, step by step, into a **multi-tenant,
authenticated, guard-railed, observable, evaluable, and monetizable AI-agent
SaaS** — all grounded in **PostgreSQL + pgvector**, served over a clean
**FastAPI** HTTP API.

Each stage is its own runnable folder that builds on the previous one. You can
open any stage and see *exactly* what that one concept adds, with nothing hidden.

```
Stage 1  Agent loop + tools          →  "it can act"
Stage 2  Multi-agent orchestration   →  "agents collaborate"
Stage 3  Memory (Postgres + pgvector)→  "it remembers"
Stage 4  Guardrails + RBAC           →  "it's safe"
Stage 5  Evals + observability       →  "we know how good / fast / costly it is"
Stage 6  Production repo + HTTP API   →  "it's a service"
Stage 7  Auth + multi-tenancy + rate →  "it's a multi-tenant SaaS"
Stage 8  Plans + billing + flags      →  "it's a billable product"
```

The running example throughout is a **Creator Orchestrator**: agents that
research a topic, write a draft, and review it — but the architecture is
general-purpose.

---

## 📑 Table of Contents
- [Why this exists](#-why-this-exists)
- [The eight stages](#-the-eight-stages)
- [Architecture at a glance](#-architecture-at-a-glance)
- [Tech stack](#-tech-stack)
- [Quickstart](#-quickstart-run-the-final-stage)
- [The unified request flow](#-the-unified-request-flow-stage-8)
- [Data model](#-data-model-one-trace-per-run_id)
- [What you'll learn](#-what-youll-learn)
- [Notes & caveats](#-notes--caveats)

---

## 🎯 Why this exists

Most "AI agent" tutorials stop at a single prompt loop. Real products need
memory, safety, evaluation, observability, an API, authentication, tenancy,
rate limits, and billing. This repo shows **how all of those layers fit
together** — and, crucially, builds them in the *order a real team would*, so
each layer is understandable on its own before the next is added.

Three principles run through every stage:

- **Postgres is the single source of truth.** No local JSON files, no ad-hoc
  state. Sessions, memory, runs, guardrail events, evals, usage — all in one DB.
- **Cross-cutting concerns are first-class, not afterthoughts.** Guardrails,
  evals, and observability live in their own packages and are wired *around*
  the model, not sprinkled into prompts.
- **Everything is verifiable.** Every stage was run end-to-end and its behavior
  confirmed in the database.

---

## 🪜 The eight stages

| Stage | Folder | What it adds | Key building blocks |
|:-----:|--------|--------------|---------------------|
| **1** | [`stage-1-core-agent-with-tools`](stage-1-core-agent-with-tools/) | A single agent loop that can call tools | tool registry · `calculator` · `weather` · `word_count` |
| **2** | [`stage-2-multi-agent-systems`](stage-2-multi-agent-systems/) | Specialist agents + two orchestration styles | `BaseAgent` · Research/Writer/Reviewer · code-driven & LLM-driven orchestrators |
| **3** | [`stage-3-memory-and-rag`](stage-3-memory-and-rag/) | Real memory in Postgres | short-term (sessions/messages) · long-term semantic (pgvector) · episodic (runs/events) |
| **4** | [`stage-4-guardrails`](stage-4-guardrails/) | Safety & policy at three layers | pre-LLM (PII + injection) · post-LLM (brand policy) · tool **RBAC** |
| **5** | [`stage-5-evals-and-observability`](stage-5-evals-and-observability/) | Measuring quality, speed & cost | eval harness · rule metrics · **LLM-as-a-judge** · latency/token/cost tracing |
| **6** | [`stage-6-production-repo-and-api`](stage-6-production-repo-and-api/) | A real repo + HTTP service | **FastAPI** (`/api/orchestrate`) · Docker · tests · docs · scripts |
| **7** | [`stage-7-auth-multitenant-and-rate-limiting`](stage-7-auth-multitenant-and-rate-limiting/) | SaaS security | **JWT** + API keys · tenants/users · per-tenant **rate limiting** (429) |
| **8** | [`stage-8-pricing-billing-and-feature-flags`](stage-8-pricing-billing-and-feature-flags/) | The business layer | plans & subscriptions · usage metering · **quota** (402) · feature flags · Stripe-ready |

> 💡 **Each later stage contains all the earlier ones.** Stage 8 is the complete
> system; Stages 1–7 are the story of how it got there.

---

## 🏗 Architecture at a glance

The final system, as a single picture:

```
                          ┌─────────────────────────────────────────┐
   Client ── HTTP ──▶     │            FastAPI  (app/)                │
   (JWT / API key)        │   /auth/token   /api/orchestrate         │
                          └──────────────────┬──────────────────────┘
                                             │
         ┌───────────────────────────────────┼───────────────────────────────────┐
         ▼                ▼                    ▼                ▼                   ▼
     Auth (S7)      Rate limit (S7)      Quota (S8)      Feature flags (S8)   Metering (S8)
     JWT→tenant       429 / velocity       402 / volume    per-tenant toggles  VIDEO_INGESTED
         │
         ▼
   ┌─────────────────────── Orchestrator (S2) ───────────────────────┐
   │   Research ─▶ Write ─▶ Review     (agents + tools, S1)            │
   │       │ pre-LLM guard (S4)  ·  tool RBAC (S4)  ·  post-LLM (S4)   │
   └───────┬──────────────────────────────────────────────────────────┘
           │
           ▼
   Memory (S3)            Observability + Evals (S5)
   sessions / messages    latency · tokens · cost · scores
   memories (pgvector)
   runs / events
           │
           ▼
   ┌──────────────────────── PostgreSQL + pgvector ─────────────────────────┐
   │  one source of truth — every signal joined by run_id / tenant_id        │
   └─────────────────────────────────────────────────────────────────────────┘
```

---

## 🧰 Tech stack

| Concern | Choice |
|---|---|
| Language | Python 3.11 |
| LLM | OpenAI (`gpt-4o` orchestrator, `gpt-4o-mini` agents), `text-embedding-3-large` @ 1536-dim |
| Data & vectors | PostgreSQL 17 + **pgvector** (HNSW cosine index) |
| DB driver | `psycopg` 3 |
| API | **FastAPI** + Uvicorn |
| Auth | JWT (`python-jose`) + `bcrypt`, API keys (SHA-256) |
| Config | `pydantic-settings` |
| Tests | `pytest` (+ FastAPI `TestClient`) |
| Packaging | Docker + docker-compose |

---

## 🚀 Quickstart (run the final stage)

The latest stage is the complete platform. Everything else is the same pattern,
fewer layers.

```bash
git clone https://github.com/polranirav/AI-Agent-Lab.git
cd AI-Agent-Lab/stage-8-pricing-billing-and-feature-flags

# 1. Python env
python3.11 -m venv ../venv && source ../venv/bin/activate
pip install -r requirements.txt

# 2. Configure (needs an OpenAI key + a pgvector-enabled Postgres)
cp .env.example .env        # then fill OPENAI_API_KEY and DATABASE_URL

# 3. Set up the database
python -m scripts.migrate   # apply migrations 001–005
python -m scripts.seed      # roles, policies, demo tenant + user, plans

# 4. Run the API
uvicorn app.main:app --reload
```

Try it:

```bash
# health
curl localhost:8000/health

# log in (demo user) → JWT
curl -X POST localhost:8000/auth/token \
  -d 'username=founder@acme.test&password=password123'

# run the agent pipeline (use the token from above)
curl -X POST localhost:8000/api/orchestrate \
  -H "Authorization: Bearer <TOKEN>" \
  -H 'content-type: application/json' \
  -d '{"topic":"AI agents for small business","brief":"Audience: SMB owners. Tone: practical."}'
```

Interactive API docs (auto-generated): **http://localhost:8000/docs**

> 🐘 No Postgres handy? `cd infra && docker compose up --build` starts the API
> plus a pgvector Postgres with migrations applied.

---

## 🔄 The unified request flow (Stage 8)

A single `POST /api/orchestrate` request touches **every stage**:

```
1. Auth            JWT / API key  →  user_id + tenant_id          (Stage 7)
2. Rate limit      429 if too many requests this minute           (Stage 7)
3. Quota           402 if the plan's monthly quota is used up      (Stage 8)
4. Feature flags   configure model/tools for this tenant           (Stage 8)
5. Metering        record 1 VIDEO_INGESTED usage event             (Stage 8)
6. Guardrails IN   redact PII, block prompt injection              (Stage 4)
7. Orchestrate     Research → Write → Review (+ tool RBAC)         (Stages 1–2,4)
8. Memory          persist session, messages, facts, run timeline  (Stage 3)
9. Guardrails OUT  enforce brand policy on the output              (Stage 4)
10. Observability  latency, tokens, cost recorded on the run        (Stage 5)
```

**429 vs 402** is a deliberate distinction: 429 = too *fast* (velocity),
402 = plan quota *used up* (volume).

---

## 🗄 Data model (one trace per `run_id`)

| Table | Stage | Purpose |
|---|:--:|---|
| `sessions`, `messages` | 3 | short-term conversation memory |
| `memories` | 3 | long-term semantic memory (pgvector embeddings) |
| `runs`, `events` | 3 / 5 | episodic timeline + per-run metrics (`runs.metadata`) |
| `guardrail_policies`, `guardrail_events` | 4 | safety config + every guardrail decision |
| `roles`, `user_roles`, `tool_policies` | 4 | tool RBAC |
| `eval_results` | 5 | quality + completion scores |
| `tenants`, `users`, `user_tenants`, `api_keys` | 7 | identity & multi-tenancy |
| `api_usage_counters` | 7 | rate-limit windows |
| `plans`, `subscriptions`, `billing_usage` | 8 | pricing, metering, billing |
| `feature_flags` | 8 | per-tenant rollout toggles |

Because everything is keyed by `run_id` (and `tenant_id`), you can join the
agent's behavior, its guardrail decisions, its cost, and its eval scores into a
single timeline for any request.

---

## 🎓 What you'll learn

- How to structure an **agent loop** with tool calling, and grow it into a
  **multi-agent orchestrator** (both deterministic and LLM-driven).
- How to give agents **real memory** with Postgres + pgvector, and when semantic
  search actually helps.
- How to treat **guardrails as execution logic** — input, output, and tool
  layers — with DB-backed, auditable policies.
- How to **evaluate** agents (rule-based + LLM-as-a-judge) and instrument
  **latency, token, and cost** observability.
- How to wrap it all in a **FastAPI service** with Docker, tests, and docs.
- How to make it a **SaaS**: JWT auth, tenant isolation, rate limiting, plans,
  usage-based billing, and feature flags.

---

## 📝 Notes & caveats

- **Educational project.** Each stage favors clarity over completeness; the code
  is meant to be read and understood, not dropped into production unchanged.
- **`web_search` is simulated.** A fake search tool with a few hardcoded topics
  keeps the project offline/free. Swapping in a real search API (Tavily/Brave/
  SerpAPI) is a clean, isolated change.
- **Stripe is scaffolded, not wired.** Stage 8 ships a dry-run usage reporter
  over `billing_usage`; connecting real Stripe credentials is the next step.
- **Secrets stay local.** Every stage's `.env` is gitignored; only
  `.env.example` templates are committed.

---

## 🗺 Roadmap

- Replace the simulated `web_search` with a real search provider.
- Wire `scripts/report_usage_to_stripe.py` to live Stripe Meter API.
- Optional: enable Postgres **Row-Level Security** for hard tenant isolation
  (the DB layer is already RLS-ready).
- Optional: export observability to OpenTelemetry / Grafana.

---

<div align="center">

**Built stage by stage — from a single agent loop to a full enterprise AI-agent SaaS.**

If this helped you understand how agent platforms fit together, a ⭐ is appreciated.

</div>
