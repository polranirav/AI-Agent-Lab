"""Per-tenant feature flags.

Roll out new models, tools, or capabilities to specific tenants at runtime
without redeploying — the same principle as LaunchDarkly, backed by Postgres.
"""

from feature_flags import service

__all__ = ["service"]
