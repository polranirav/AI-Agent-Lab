-- Stage 8: Plans, subscriptions, usage metering, and feature flags.

-- Billing plans (free, pro, enterprise)
CREATE TABLE IF NOT EXISTS plans (
    id           UUID PRIMARY KEY,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    name         TEXT NOT NULL UNIQUE,        -- 'free', 'pro', 'enterprise'
    display_name TEXT NOT NULL,
    metadata     JSONB DEFAULT '{}'::jsonb    -- pricing details, quotas, etc.
);

-- Tenant subscriptions to plans
CREATE TABLE IF NOT EXISTS subscriptions (
    id                   UUID PRIMARY KEY,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    tenant_id            UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plan_id              UUID NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
    status               TEXT NOT NULL DEFAULT 'active',  -- 'active','trialing','past_due','canceled'
    current_period_start TIMESTAMPTZ NOT NULL,
    current_period_end   TIMESTAMPTZ NOT NULL,
    external_ref         TEXT,                 -- e.g. Stripe subscription ID
    metadata             JSONB DEFAULT '{}'::jsonb
);
-- One active subscription per tenant.
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_subscription_per_tenant
    ON subscriptions (tenant_id) WHERE status = 'active';

-- Usage counters per tenant & billing period & metric
CREATE TABLE IF NOT EXISTS billing_usage (
    id           BIGSERIAL PRIMARY KEY,
    tenant_id    UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    period_start TIMESTAMPTZ NOT NULL,
    period_end   TIMESTAMPTZ NOT NULL,
    metric       TEXT NOT NULL,        -- 'VIDEO_INGESTED', 'TOKENS', etc.
    units        BIGINT NOT NULL DEFAULT 0,
    last_updated TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata     JSONB DEFAULT '{}'::jsonb
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_billing_usage_tenant_metric_period
    ON billing_usage (tenant_id, metric, period_start, period_end);

-- Feature flags per tenant
CREATE TABLE IF NOT EXISTS feature_flags (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    flag_name   TEXT NOT NULL,
    enabled     BOOLEAN NOT NULL DEFAULT false,
    metadata    JSONB DEFAULT '{}'::jsonb,
    UNIQUE (tenant_id, flag_name)
);
