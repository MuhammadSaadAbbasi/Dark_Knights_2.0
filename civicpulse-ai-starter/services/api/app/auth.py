import hashlib
import hmac
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .db.users import get_user
from .db.users import create_user


logger = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)
PASSWORD_ITERATIONS = 310_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(candidate.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "").strip()
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET must be configured with at least 32 characters.")
    return secret


def create_access_token(user: dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(
        minutes=max(5, int(os.getenv("ACCESS_TOKEN_MINUTES", "60")))
    )
    return jwt.encode(
        {
            "sub": str(user["id"]),
            "username": user["username"],
            "role": user["role"],
            "iat": now,
            "exp": expires,
        },
        _jwt_secret(),
        algorithm="HS256",
    )


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    user = get_user(username.strip())
    if not user or not user["is_active"] or not verify_password(
        password, user["password_hash"]
    ):
        return None
    return user


def require_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict[str, Any]:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = jwt.decode(credentials.credentials, _jwt_secret(), algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The access token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if claims.get("role") not in {"user", "admin"} or not claims.get("sub"):
        raise HTTPException(status_code=403, detail="User permissions are required.")
    user = get_user(str(claims.get("username", "")))
    if not user or not user["is_active"] or str(user["id"]) != str(claims["sub"]):
        raise HTTPException(status_code=401, detail="User is inactive.")
    return user


def ensure_bootstrap_admin() -> None:
    username = os.getenv("ADMIN_USERNAME", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not username or not password:
        logger.warning(
            "ADMIN_USERNAME and ADMIN_PASSWORD are not configured; create an admin account before login."
        )
        return
    if len(password) < 8:
        raise RuntimeError("ADMIN_PASSWORD must contain at least 8 characters.")
    if get_user(username):
        return
    create_user(
        username=username,
        password_hash=hash_password(password),
        role="admin",
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict[str, Any]:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = jwt.decode(
            credentials.credentials,
            _jwt_secret(),
            algorithms=["HS256"],
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The access token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if claims.get("role") != "admin" or not claims.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions are required.",
        )
    user = get_user(str(claims["username"]))
    if not user or not user["is_active"] or str(user["id"]) != str(claims["sub"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive.")
    return user
