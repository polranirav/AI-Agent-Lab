-- Stage 5: Evaluation results, stored at run-level / agent-level / message-level.
-- One row per evaluator per target. Keyed by run_id so it joins with the same
-- trace that runs, events, and guardrail_events use.

CREATE TABLE IF NOT EXISTS eval_results (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    run_id      UUID REFERENCES runs(id) ON DELETE CASCADE,
    session_id  UUID REFERENCES sessions(id) ON DELETE SET NULL,
    evaluator   TEXT NOT NULL,        -- e.g. 'task_completion', 'brand_fit_judge'
    scope       TEXT NOT NULL,        -- 'run', 'agent', 'message'
    target      TEXT NOT NULL,        -- which agent or step (e.g. 'WriterAgent')
    score       DOUBLE PRECISION,     -- numeric score 0-1 or 0-5
    label       TEXT,                 -- optional label like 'pass'/'fail'
    details     JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_eval_results_run ON eval_results(run_id);
CREATE INDEX IF NOT EXISTS idx_eval_results_evaluator ON eval_results(evaluator);
