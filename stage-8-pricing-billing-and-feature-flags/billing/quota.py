"""Quota enforcement — connect usage metering to plan limits.

Returns HTTP 402 (Payment Required) when a tenant has no active subscription or
has exceeded its plan quota for the current billing period. This is distinct
from the Stage 7 rate limiter (429), which constrains request *velocity*; quota
constrains billable *volume* per plan.
"""

from fastapi import HTTPException, status

from billing.plans import get_active_subscription, get_video_quota
from billing.meter import current_billing_period
from memory.db import get_cursor


def enforce_video_quota(tenant_id: str) -> None:
    sub = get_active_subscription(tenant_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="No active subscription",
        )

    quota = get_video_quota(sub["plan_metadata"])
    if quota <= 0:
        return  # unlimited plan

    period_start, period_end = current_billing_period()
    with get_cursor(tenant_id=tenant_id) as cur:
        cur.execute(
            """
            SELECT COALESCE(SUM(units), 0)
            FROM billing_usage
            WHERE tenant_id = %s
              AND metric = 'VIDEO_INGESTED'
              AND period_start = %s
              AND period_end   = %s
            """,
            (tenant_id, period_start, period_end),
        )
        used = cur.fetchone()[0]

    if used >= quota:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Video quota exceeded for current billing period "
                   f"({used}/{quota}). Upgrade your plan.",
        )
