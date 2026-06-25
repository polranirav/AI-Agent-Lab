"""Seed initial roles, user_roles, tool_policies, and the brand policy.

Idempotent — safe to run multiple times.

Usage:
    python -m scripts.seed
"""

import psycopg

from app.config import settings

SEED_SQL = """
-- Roles
INSERT INTO roles (name) VALUES ('creator'), ('operator'), ('admin')
ON CONFLICT (name) DO NOTHING;

-- Example user -> role mappings
INSERT INTO user_roles (user_id, role_id)
SELECT 'user:marcus', id FROM roles WHERE name = 'creator'
ON CONFLICT DO NOTHING;
INSERT INTO user_roles (user_id, role_id)
SELECT 'user:priya', id FROM roles WHERE name = 'operator'
ON CONFLICT DO NOTHING;
INSERT INTO user_roles (user_id, role_id)
SELECT 'user:eval', id FROM roles WHERE name = 'creator'
ON CONFLICT DO NOTHING;

-- Tool policies: creators get safe tools; only operators may schedule_post
INSERT INTO tool_policies (tool_name, role_id, allowed, require_approval)
SELECT 'web_search', id, true, false FROM roles WHERE name = 'creator';
INSERT INTO tool_policies (tool_name, role_id, allowed, require_approval)
SELECT 'calculator', id, true, false FROM roles WHERE name = 'creator';
INSERT INTO tool_policies (tool_name, role_id, allowed, require_approval)
SELECT 'schedule_post', id, true, false FROM roles WHERE name = 'operator';

-- Output brand policy
INSERT INTO guardrail_policies (name, kind, config)
VALUES (
  'creator_brand_policy',
  'output',
  '{"blocked_terms": ["revolutionary", "100% guarantee"], "required_terms": ["This is not financial advice."]}'::jsonb
)
ON CONFLICT (name) DO UPDATE SET config = EXCLUDED.config;
"""


def main() -> None:
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(SEED_SQL)
        conn.commit()
    print("Seed complete: roles, user_roles, tool_policies, brand policy.")


if __name__ == "__main__":
    main()
