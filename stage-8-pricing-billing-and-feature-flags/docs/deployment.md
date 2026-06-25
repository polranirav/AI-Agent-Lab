# Deployment

## Prerequisites
- Python 3.11+
- PostgreSQL with the `pgvector` extension
- An OpenAI API key

## 1. Configure environment
Copy `.env.example` to `.env` and fill in:
```
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:pass@host:5432/dbname
ORCHESTRATOR_MODEL=gpt-4o
AGENT_MODEL=gpt-4o-mini
```

## 2. Install dependencies
```bash
pip install -r requirements.txt
```

## 3. Set up the database
```bash
python -m scripts.migrate   # apply migrations/001..003
python -m scripts.seed      # roles, tool policies, brand policy
```

## 4. Run locally
```bash
uvicorn app.main:app --reload
# health:   curl http://localhost:8000/health
# docs:     open http://localhost:8000/docs
```

## 5. Run with Docker
```bash
cd infra
docker compose up --build
```
This starts:
- `db` — Postgres + pgvector (migrations auto-applied on first boot)
- `api` — the FastAPI service on port 8000

## 6. Tests
```bash
pytest -q
```

## Health probes
Use `scripts/healthcheck.py` (exits non-zero on failure) for container/k8s
liveness probes:
```bash
python -m scripts.healthcheck
```
