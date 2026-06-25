"""Auth tests — password hashing, JWT, and the login endpoint.

The login test requires the demo user to be seeded (scripts/seed.py).
"""

from fastapi.testclient import TestClient

from app.main import app
from app.auth import hash_password, verify_password, create_access_token, get_current_principal

client = TestClient(app)


def test_password_hash_roundtrip():
    h = hash_password("password123")
    assert h != "password123"          # never store plaintext
    assert verify_password("password123", h) is True
    assert verify_password("wrong", h) is False


def test_jwt_encodes_identity():
    import asyncio
    token = create_access_token({"sub": "user-1", "tenant_id": "tenant-1"})
    principal = asyncio.run(get_current_principal(token))
    assert principal == {"user_id": "user-1", "tenant_id": "tenant-1"}


def test_login_bad_credentials_rejected():
    resp = client.post("/auth/token",
                       data={"username": "founder@acme.test", "password": "WRONG"})
    assert resp.status_code == 401


def test_login_succeeds_and_protects_orchestrate():
    # Demo user must be seeded. Get a token, then call the protected endpoint
    # with a missing field -> 422 (proves auth passed, validation runs after).
    login = client.post("/auth/token",
                        data={"username": "founder@acme.test", "password": "password123"})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    resp = client.post(
        "/api/orchestrate",
        headers={"Authorization": f"Bearer {token}"},
        json={"brief": "missing topic"},   # invalid body on purpose
    )
    assert resp.status_code == 422        # authenticated, but body invalid
