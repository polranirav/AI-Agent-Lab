# API Reference

Base URL (local): `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs` (Swagger UI, auto-generated)

## Authentication (Stage 7)

All `/api/*` routes require a **Bearer JWT**. Obtain one from `/auth/token`.

### `POST /auth/token`
OAuth2 password grant (form-encoded, not JSON).

```bash
curl -X POST localhost:8000/auth/token \
  -d 'username=founder@acme.test&password=password123'
# -> { "access_token": "<jwt>", "token_type": "bearer" }
```

The JWT carries `user_id` (sub) and `tenant_id`. Send it on protected calls:
```
Authorization: Bearer <jwt>
```

**Multi-tenancy:** identity is taken from the token, never the request body.
Every session/run is tagged with the caller's `tenant_id`.

**Rate limiting:** each tenant+user is limited to `RATE_LIMIT_PER_MINUTE`
requests per minute. Over the limit returns **429** with a `Retry-After` header.

**M2M:** machine clients may instead send an API key as `Authorization: Bearer
<raw_key>` (only the SHA-256 hash is stored). See `app/api_key_auth.py`.

## `GET /health`

Liveness probe.

**Response 200**
```json
{ "status": "ok" }
```

## `POST /api/orchestrate`

Run the full content pipeline (research → write → review) and return the
generated artifacts plus run metrics.

**Request body**
```json
{
  "topic": "AI agents for small business",
  "brief": "Audience: SMB owners. Tone: practical, no hype.",
  "user_id": "user:marcus"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `topic` | string | yes | What to create content about |
| `brief` | string | no | Audience/tone/constraints |
| `user_id` | string | no | Drives tool RBAC (e.g. `user:marcus`) |

**Response 200**
```json
{
  "run_id": "uuid",
  "session_id": "uuid",
  "artifacts": [
    { "kind": "post", "content": "..." }
  ],
  "metrics": { "latency_ms": 24550.0, "token_total": 3902, "cost_usd": 0.0011 }
}
```

`artifacts[].kind` is one of `post`, `email`, `clip`.

**Errors**
- `422` — request failed validation (e.g. missing `topic`).
- `500` — internal error (the run is marked `error` in the `runs` table).

## Inspecting a run

Everything is keyed by `run_id`:
```sql
SELECT * FROM events         WHERE run_id = '<run_id>' ORDER BY created_at;
SELECT * FROM guardrail_events WHERE run_id = '<run_id>';
SELECT * FROM eval_results   WHERE run_id = '<run_id>';
SELECT metadata FROM runs    WHERE id = '<run_id>';
```
