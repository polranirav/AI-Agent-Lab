"""Billing tests — metering, plan lookup, and quota enforcement.

Require the demo tenant + free plan to be seeded (scripts/seed.py).
"""

import pytest
from fastapi import HTTPException

from billing.meter import record_usage, current_billing_period
from billing.plans import get_active_subscription, get_video_quota
from billing.quota import enforce_video_quota
from memory.db import get_cursor

DEMO_TENANT = "11111111-1111-1111-1111-111111111111"


def _used_videos(tenant_id: str) -> int:
    ps, pe = current_billing_period()
    with get_cursor() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(units),0) FROM billing_usage "
            "WHERE tenant_id=%s AND metric='VIDEO_INGESTED' "
            "AND period_start=%s AND period_end=%s",
            (tenant_id, ps, pe),
        )
        return cur.fetchone()[0]


def test_demo_tenant_has_active_free_plan():
    sub = get_active_subscription(DEMO_TENANT)
    assert sub is not None
    assert sub["plan_name"] == "free"
    assert get_video_quota(sub["plan_metadata"]) == 5


def test_record_usage_increments():
    before = _used_videos(DEMO_TENANT)
    record_usage(DEMO_TENANT, "VIDEO_INGESTED", 1)
    after = _used_videos(DEMO_TENANT)
    assert after == before + 1


def test_quota_enforced_when_over_limit():
    # Push usage to the quota, then enforcement must raise 402.
    sub = get_active_subscription(DEMO_TENANT)
    quota = get_video_quota(sub["plan_metadata"])
    used = _used_videos(DEMO_TENANT)
    if used < quota:
        record_usage(DEMO_TENANT, "VIDEO_INGESTED", quota - used)

    with pytest.raises(HTTPException) as exc:
        enforce_video_quota(DEMO_TENANT)
    assert exc.value.status_code == 402

    # Clean up so other runs/tests start fresh this period.
    with get_cursor() as cur:
        cur.execute(
            "DELETE FROM billing_usage WHERE tenant_id=%s AND metric='VIDEO_INGESTED'",
            (DEMO_TENANT,),
        )
