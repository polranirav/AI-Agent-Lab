"""Usage metering — record billable events per tenant per billing period.

A billable event for the Creator Orchestrator is one campaign/video ingested.
Usage is aggregated into `billing_usage` (one row per tenant/metric/period),
which is the table a Stripe integration later reports from.
"""

from datetime import datetime, timezone
from typing import Literal, Tuple

from memory.db import get_cursor

Metric = Literal["VIDEO_INGESTED", "TOKENS"]


def current_billing_period() -> Tuple[datetime, datetime]:
    """Calendar-month billing window [start, end)."""
    now = datetime.now(timezone.utc)
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if period_start.month == 12:
        period_end = period_start.replace(year=period_start.year + 1, month=1)
    else:
        period_end = period_start.replace(month=period_start.month + 1)
    return period_start, period_end


def record_usage(tenant_id: str, metric: Metric, units: int) -> None:
    """Increment a tenant's usage for a metric in the current billing period."""
    period_start, period_end = current_billing_period()
    with get_cursor(tenant_id=tenant_id) as cur:
        cur.execute(
            """
            INSERT INTO billing_usage (tenant_id, period_start, period_end, metric, units)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (tenant_id, metric, period_start, period_end)
            DO UPDATE SET units = billing_usage.units + EXCLUDED.units,
                          last_updated = now()
            """,
            (tenant_id, period_start, period_end, metric, units),
        )
