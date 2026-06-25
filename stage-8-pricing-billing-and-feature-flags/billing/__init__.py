"""Billing layer for Stage 8.

Turns the multi-tenant platform into a billable SaaS:
  - meter  : record billable usage events per tenant per period
  - plans  : read a tenant's active subscription and its plan quotas
  - quota  : enforce per-plan limits (HTTP 402 when exceeded)

All grounded in Postgres; a Stripe integration reports `billing_usage` later.
"""

from billing import meter, plans, quota

__all__ = ["meter", "plans", "quota"]
