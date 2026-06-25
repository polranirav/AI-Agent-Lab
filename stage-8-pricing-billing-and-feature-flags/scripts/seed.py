"""Seed roles, tool policies, the brand policy, and a demo tenant + user.

Idempotent — safe to run multiple times.

Demo login (Stage 7):
    email:    founder@acme.test
    password: password123

Usage:
    python -m scripts.seed
"""

import json
from datetime import datetime, timedelta, timezone

import psycopg

from app.config import settings
from app.auth import hash_password

# Fixed IDs so the demo is predictable across re-seeds.
DEMO_TENANT_ID = "11111111-1111-1111-1111-111111111111"
DEMO_USER_ID = "22222222-2222-2222-2222-222222222222"
DEMO_EMAIL = "founder@acme.test"
DEMO_PASSWORD = "password123"

FREE_PLAN_ID = "33333333-3333-3333-3333-333333333333"
PRO_PLAN_ID = "44444444-4444-4444-4444-444444444444"
SUBSCRIPTION_ID = "55555555-5555-5555-5555-555555555555"

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

-- The demo user (UUID below) gets the creator role so its authenticated runs
-- can use safe tools (web_search, calculator).
INSERT INTO user_roles (user_id, role_id)
SELECT '22222222-2222-2222-2222-222222222222', id FROM roles WHERE name = 'creator'
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


# Parameterized statements must run one at a time (no multi-command prepares).
AUTH_STATEMENTS = [
    "INSERT INTO tenants (id, name) VALUES (%(tenant_id)s, 'Acme Creators') "
    "ON CONFLICT (id) DO NOTHING",
    "INSERT INTO users (id, email, password_hash) "
    "VALUES (%(user_id)s, %(email)s, %(password_hash)s) "
    "ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash",
    "INSERT INTO user_tenants (user_id, tenant_id, role) "
    "VALUES (%(user_id)s, %(tenant_id)s, 'owner') "
    "ON CONFLICT (user_id, tenant_id) DO NOTHING",
]


# Stage 8: plans + a subscription for the demo tenant (on the free plan).
BILLING_STATEMENTS = [
    "INSERT INTO plans (id, name, display_name, metadata) "
    "VALUES (%(free_plan_id)s, 'free', 'Free', %(free_meta)s::jsonb) "
    "ON CONFLICT (name) DO UPDATE SET metadata = EXCLUDED.metadata",
    "INSERT INTO plans (id, name, display_name, metadata) "
    "VALUES (%(pro_plan_id)s, 'pro', 'Pro', %(pro_meta)s::jsonb) "
    "ON CONFLICT (name) DO UPDATE SET metadata = EXCLUDED.metadata",
    # One active subscription for the demo tenant on the free plan.
    "INSERT INTO subscriptions "
    "(id, tenant_id, plan_id, status, current_period_start, current_period_end) "
    "SELECT %(sub_id)s, %(tenant_id)s, %(free_plan_id)s, 'active', "
    "       %(period_start)s, %(period_end)s "
    "WHERE NOT EXISTS (SELECT 1 FROM subscriptions "
    "                  WHERE tenant_id = %(tenant_id)s AND status = 'active')",
]


def main() -> None:
    now = datetime.now(timezone.utc)
    params = {
        "tenant_id": DEMO_TENANT_ID,
        "user_id": DEMO_USER_ID,
        "email": DEMO_EMAIL,
        "password_hash": hash_password(DEMO_PASSWORD),
        "free_plan_id": FREE_PLAN_ID,
        "pro_plan_id": PRO_PLAN_ID,
        "sub_id": SUBSCRIPTION_ID,
        "free_meta": json.dumps({"video_quota": 5, "seats": 1}),
        "pro_meta": json.dumps({"video_quota": 50, "seats": 5}),
        "period_start": now,
        "period_end": now + timedelta(days=30),
    }
    with psycopg.connect(settings.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(SEED_SQL)
            for stmt in AUTH_STATEMENTS + BILLING_STATEMENTS:
                cur.execute(stmt, params)
        conn.commit()
    print("Seed complete: roles, tool policies, brand policy, plans + subscription.")
    print(f"Demo login -> email: {DEMO_EMAIL}  password: {DEMO_PASSWORD}")
    print("Demo tenant is on the FREE plan (5 videos/month).")


if __name__ == "__main__":
    main()
