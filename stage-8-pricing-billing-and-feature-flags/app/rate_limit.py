"""Per-tenant / per-user rate limiting, backed by Postgres counters.

A sliding-by-minute window: one counter row per (tenant, user, minute). Each
request upserts and increments it; over the limit returns HTTP 429. The
interface is deliberately simple so it can later be swapped for Redis or an API
gateway without changing callers.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.config import settings
from memory.db import get_cursor


def floor_to_minute(dt: datetime) -> datetime:
    return dt.replace(second=0, microsecond=0)


def enforce_rate_limit(tenant_id: str, user_id: Optional[str]) -> int:
    """Increment the per-minute counter; raise 429 if over the limit.

    Returns the current request count in this window (for observability/tests).
    """
    now = datetime.now(timezone.utc)
    period_start = floor_to_minute(now)

    with get_cursor(tenant_id=tenant_id) as cur:
        cur.execute(
            """
            INSERT INTO api_usage_counters
                (tenant_id, user_id, period_start, period, requests)
            VALUES (%s, %s, %s, 'minute', 1)
            ON CONFLICT (tenant_id, user_id, period, period_start)
            DO UPDATE SET requests = api_usage_counters.requests + 1
            RETURNING requests
            """,
            (tenant_id, user_id, period_start),
        )
        requests = cur.fetchone()[0]

    if requests > settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"},
        )
    return requests
