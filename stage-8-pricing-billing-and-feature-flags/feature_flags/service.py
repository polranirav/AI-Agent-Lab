"""Feature flag helpers: read and toggle flags per tenant."""

from memory.db import get_cursor


def is_feature_enabled(tenant_id: str, flag_name: str) -> bool:
    """Return True only if the flag exists and is enabled for this tenant."""
    with get_cursor(tenant_id=tenant_id) as cur:
        cur.execute(
            "SELECT enabled FROM feature_flags WHERE tenant_id = %s AND flag_name = %s",
            (tenant_id, flag_name),
        )
        row = cur.fetchone()
    return bool(row and row[0])


def set_feature_flag(tenant_id: str, flag_name: str, enabled: bool) -> None:
    """Enable/disable a flag for a tenant (idempotent upsert)."""
    with get_cursor(tenant_id=tenant_id) as cur:
        cur.execute(
            """
            INSERT INTO feature_flags (tenant_id, flag_name, enabled)
            VALUES (%s, %s, %s)
            ON CONFLICT (tenant_id, flag_name)
            DO UPDATE SET enabled = EXCLUDED.enabled
            """,
            (tenant_id, flag_name, enabled),
        )
