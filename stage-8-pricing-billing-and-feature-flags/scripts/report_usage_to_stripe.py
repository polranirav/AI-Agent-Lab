"""Batch usage reporting to a billing provider (Stripe) — scaffold.

Full Stripe integration is beyond this stage's scope, but our schema is already
shaped the way Stripe expects: we aggregate `billing_usage` per tenant/period,
so a real implementation would, for each tenant:

  1. Look up the tenant's `subscriptions.external_ref` (Stripe subscription ID).
  2. Send the period's usage to Stripe's Meter API (or AI Gateway for tokens).
  3. Store the returned Stripe event ID in `billing_usage.metadata` to avoid
     double-reporting.

This script prints what *would* be reported (a dry run), so you can verify the
numbers before wiring real Stripe credentials.

Usage:
    python -m scripts.report_usage_to_stripe
"""

from billing.meter import current_billing_period
from memory.db import get_cursor


def main() -> None:
    period_start, period_end = current_billing_period()
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT bu.tenant_id, t.name, bu.metric, bu.units, s.external_ref
            FROM billing_usage bu
            JOIN tenants t ON t.id = bu.tenant_id
            LEFT JOIN subscriptions s
                   ON s.tenant_id = bu.tenant_id AND s.status = 'active'
            WHERE bu.period_start = %s AND bu.period_end = %s
            ORDER BY t.name, bu.metric
            """,
            (period_start, period_end),
        )
        rows = cur.fetchall()

    print(f"Usage to report for period {period_start:%Y-%m-%d} .. {period_end:%Y-%m-%d}")
    print("-" * 64)
    if not rows:
        print("(no usage this period)")
        return
    for tenant_id, name, metric, units, external_ref in rows:
        target = external_ref or "<no Stripe subscription linked>"
        print(f"  tenant={name:20s} metric={metric:14s} units={units:6d} -> {target}")
    print("-" * 64)
    print("DRY RUN — no data sent to Stripe. Wire the Meter API call here.")


if __name__ == "__main__":
    main()
