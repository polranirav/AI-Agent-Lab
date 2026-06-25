"""Authentication: JWT user auth (email/password -> bearer token).

Flow:
  POST /auth/token   (email + password)  -> signed JWT containing user_id+tenant_id
  Protected routes   Depends(get_current_principal)  -> {user_id, tenant_id}

Notes:
  - Passwords are hashed with bcrypt; only the hash is stored.
  - The JWT carries identity only (no secrets) and is verified on every request,
    so no server-side session storage is needed.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

from app.config import settings
from memory.db import get_cursor

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# ── Passwords ────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


# ── User lookup ──────────────────────────────────────────────────────
def get_user_by_email(email: str) -> Optional[dict]:
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, password_hash FROM users WHERE email = %s AND is_active = true",
            (email,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {"id": str(row[0]), "password_hash": row[1]}


def get_primary_tenant_id(user_id: str) -> Optional[str]:
    with get_cursor() as cur:
        cur.execute(
            "SELECT tenant_id FROM user_tenants WHERE user_id = %s LIMIT 1",
            (user_id,),
        )
        row = cur.fetchone()
    return str(row[0]) if row else None


def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return user


# ── Tokens ───────────────────────────────────────────────────────────
def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key,
                      algorithm=settings.jwt_algorithm)


async def get_current_principal(token: str = Depends(oauth2_scheme)) -> dict:
    """Validate the bearer token and return the {user_id, tenant_id} principal."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key,
                             algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        if user_id is None or tenant_id is None:
            raise credentials_error
    except JWTError:
        raise credentials_error
    return {"user_id": user_id, "tenant_id": tenant_id}


# ── Router ───────────────────────────────────────────────────────────
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 password grant: exchange email/password for a JWT."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    tenant_id = get_primary_tenant_id(user["id"])
    if not tenant_id:
        raise HTTPException(status_code=403, detail="User has no tenant")

    token = create_access_token(data={"sub": user["id"], "tenant_id": tenant_id})
    return {"access_token": token, "token_type": "bearer"}
