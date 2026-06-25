-- Stage 7: Auth, multi-tenancy, and rate limiting.

-- Tenants (organizations / accounts)
CREATE TABLE IF NOT EXISTS tenants (
    id          UUID PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    name        TEXT NOT NULL,
    metadata    JSONB DEFAULT '{}'::jsonb
);

-- Users
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_active     BOOLEAN NOT NULL DEFAULT true,
    metadata      JSONB DEFAULT '{}'::jsonb
);

-- User <-> Tenant membership with a role
CREATE TABLE IF NOT EXISTS user_tenants (
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id  UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    role       TEXT NOT NULL DEFAULT 'member',  -- 'owner', 'admin', 'member'
    PRIMARY KEY (user_id, tenant_id)
);

-- API keys for server-to-server (M2M) access. Only a hash is stored.
CREATE TABLE IF NOT EXISTS api_keys (
    id            UUID PRIMARY KEY,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id       UUID REFERENCES users(id) ON DELETE SET NULL,
    label         TEXT NOT NULL,
    key_hash      TEXT NOT NULL,        -- sha256 of the raw key (never store raw)
    is_revoked    BOOLEAN NOT NULL DEFAULT false,
    last_used_at  TIMESTAMPTZ,
    metadata      JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);

-- Add tenant/user context to existing tables (idempotent).
ALTER TABLE sessions         ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE runs             ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE messages         ADD COLUMN IF NOT EXISTS user_id   UUID;
ALTER TABLE memories         ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE guardrail_events ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE eval_results     ADD COLUMN IF NOT EXISTS tenant_id UUID;

-- Rate limiting: request/token counters per tenant/user/period.
CREATE TABLE IF NOT EXISTS api_usage_counters (
    id           BIGSERIAL PRIMARY KEY,
    tenant_id    UUID NOT NULL,
    user_id      UUID,
    period_start TIMESTAMPTZ NOT NULL,   -- floored to minute/hour/day
    period       TEXT NOT NULL,          -- 'minute', 'hour', 'day'
    requests     INTEGER NOT NULL DEFAULT 0,
    tokens       BIGINT NOT NULL DEFAULT 0
);

-- Unique key so the rate limiter can UPSERT a single counter row per window.
CREATE UNIQUE INDEX IF NOT EXISTS uq_api_usage_counter
    ON api_usage_counters (tenant_id, user_id, period, period_start)
    NULLS NOT DISTINCT;
