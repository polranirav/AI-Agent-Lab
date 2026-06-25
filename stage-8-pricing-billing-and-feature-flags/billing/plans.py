"""Plans & subscriptions — read a tenant's active plan and its quotas."""

from datetime import datetime, timezone
from typing import Optional

from memory.db import get_cursor


def get_active_subscription(tenant_id: str) -> Optional[dict]:
    """Return the tenant's currently-active subscription + plan, or None."""
    now = datetime.now(timezone.utc)
    with get_cursor(tenant_id=tenant_id) as cur:
        cur.execute(
            """
            SELECT s.id, p.name, p.metadata,
                   s.current_period_start, s.current_period_end
            FROM subscriptions s
            JOIN plans p ON s.plan_id = p.id
            WHERE s.tenant_id = %s
              AND s.status = 'active'
              AND s.current_period_start <= %s
              AND s.current_period_end   > %s
            LIMIT 1
            """,
            (tenant_id, now, now),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "subscription_id": str(row[0]),
        "plan_name": row[1],
        "plan_metadata": row[2] or {},
        "period_start": row[3],
        "period_end": row[4],
    }


def get_video_quota(plan_metadata: dict) -> int:
    """Monthly VIDEO_INGESTED quota for a plan (0 or missing => unlimited)."""
    return int(plan_metadata.get("video_quota", 0))
