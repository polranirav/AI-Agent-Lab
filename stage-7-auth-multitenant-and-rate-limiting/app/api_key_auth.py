"""API key authentication for machine-to-machine (M2M) access.

Clients send `Authorization: Bearer <raw_key>`. Only the SHA-256 hash of the key
is stored in the DB, so a leaked database never exposes usable keys.
"""

from hashlib import sha256
from typing import Optional

from fastapi import Header, HTTPException, status

from memory.db import get_cursor


def hash_api_key(raw_key: str) -> str:
    return sha256(raw_key.encode("utf-8")).hexdigest()


async def get_principal_from_api_key(
    authorization: Optional[str] = Header(None),
) -> dict:
    """Resolve an API key from the Authorization header to a principal."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Missing API key")

    raw_key = authorization.split(" ", 1)[1]
    key_hash = hash_api_key(raw_key)

    with get_cursor() as cur:
        cur.execute(
            """
            SELECT tenant_id, user_id FROM api_keys
            WHERE key_hash = %s AND is_revoked = false
            """,
            (key_hash,),
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE api_keys SET last_used_at = now() WHERE key_hash = %s",
                (key_hash,),
            )

    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid API key")

    tenant_id, user_id = row
    return {"user_id": str(user_id) if user_id else None,
            "tenant_id": str(tenant_id)}
