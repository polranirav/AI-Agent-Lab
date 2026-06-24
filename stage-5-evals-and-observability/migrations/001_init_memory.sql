-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Sessions (short-term memory scope)
CREATE TABLE IF NOT EXISTS sessions (
    id          UUID PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id     TEXT,                 -- optional: multi-tenant support
    topic       TEXT,                 -- e.g., blog topic or campaign name
    metadata    JSONB DEFAULT '{}'::jsonb
);

-- 2. Messages (short-term memory content)
CREATE TABLE IF NOT EXISTS messages (
    id          BIGSERIAL PRIMARY KEY,
    session_id  UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    role        TEXT NOT NULL,        -- 'user', 'assistant', 'tool', 'system'
    content     TEXT NOT NULL,
    metadata    JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_messages_session_created
    ON messages (session_id, created_at);

-- 3. Long-term semantic memory (pgvector)
-- Store facts, brand rules, approved content snippets, etc.
-- Embedding dimension 1536 (OpenAI text-embedding-3-large @ dimensions=1536)
CREATE TABLE IF NOT EXISTS memories (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    session_id  UUID,                 -- optional link to session
    user_id     TEXT,                 -- optional multi-tenant
    kind        TEXT NOT NULL,        -- 'brand', 'fact', 'clip', 'insight', etc.
    label       TEXT NOT NULL,        -- short description
    content     TEXT NOT NULL,        -- full text
    metadata    JSONB DEFAULT '{}'::jsonb,
    embedding   vector(1536)          -- pgvector column
);

CREATE INDEX IF NOT EXISTS idx_memories_kind ON memories(kind);
CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id);

-- HNSW index for fast similarity search (cosine distance)
CREATE INDEX IF NOT EXISTS idx_memories_embedding
    ON memories
    USING hnsw (embedding vector_cosine_ops);

-- 4. Episodic memory: runs and events
CREATE TABLE IF NOT EXISTS runs (
    id           UUID PRIMARY KEY,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    session_id   UUID REFERENCES sessions(id) ON DELETE SET NULL,
    orchestrator TEXT NOT NULL,       -- 'code-driven', 'llm-driven', etc.
    status       TEXT NOT NULL,       -- 'running', 'success', 'error'
    error        TEXT,                -- error message if any
    metadata     JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS events (
    id          BIGSERIAL PRIMARY KEY,
    run_id      UUID NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    agent_name  TEXT,                 -- e.g. 'ResearchAgent'
    event_type  TEXT NOT NULL,        -- 'agent_start', 'agent_end', 'tool_call', etc.
    message     TEXT,                 -- human-readable description
    payload     JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_events_run_created
    ON events (run_id, created_at);
