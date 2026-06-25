-- Guardrail configurations and logs.

CREATE TABLE IF NOT EXISTS guardrail_policies (
    id           BIGSERIAL PRIMARY KEY,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    name         TEXT NOT NULL UNIQUE,      -- e.g. 'default_creator_policy'
    kind         TEXT NOT NULL,            -- 'input', 'output', 'tool'
    config       JSONB NOT NULL            -- structured policy config
);

CREATE TABLE IF NOT EXISTS guardrail_events (
    id           BIGSERIAL PRIMARY KEY,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    run_id       UUID REFERENCES runs(id) ON DELETE SET NULL,
    session_id   UUID REFERENCES sessions(id) ON DELETE SET NULL,
    policy_name  TEXT NOT NULL,
    layer        TEXT NOT NULL,            -- 'pre-llm', 'post-llm', 'tool'
    action       TEXT NOT NULL,            -- 'allow', 'block', 'redact', 'modify', 'escalate'
    reason       TEXT NOT NULL,
    details      JSONB DEFAULT '{}'::jsonb
);

-- Tool RBAC: which roles can use which tools and what approvals are required.
CREATE TABLE IF NOT EXISTS roles (
    id           BIGSERIAL PRIMARY KEY,
    name         TEXT NOT NULL UNIQUE      -- e.g. 'creator', 'operator', 'admin'
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id      TEXT NOT NULL,
    role_id      BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS tool_policies (
    id           BIGSERIAL PRIMARY KEY,
    tool_name    TEXT NOT NULL,            -- e.g. 'schedule_post'
    role_id      BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    allowed      BOOLEAN NOT NULL DEFAULT true,
    require_approval BOOLEAN NOT NULL DEFAULT false,
    metadata     JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_tool_policies_tool_role
    ON tool_policies (tool_name, role_id);