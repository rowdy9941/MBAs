from datetime import UTC, datetime, timedelta
import base64
import hashlib
import hmac
import json
import secrets
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status

from app.config import settings


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        _, salt, digest = encoded.split("$")
        actual = hashlib.scrypt(password.encode(), salt=base64.urlsafe_b64decode(salt + "=="), n=16384, r=8, p=1)
        return hmac.compare_digest(_b64(actual), digest)
    except (ValueError, TypeError):
        return False


def issue_token(user_id: UUID, tenant_id: UUID, role: str) -> str:
    header = _b64(b'{"alg":"HS256","typ":"JWT"}')
    payload = _b64(json.dumps({"sub": str(user_id), "tenant_id": str(tenant_id), "role": role,
                               "exp": int((datetime.now(UTC) + timedelta(minutes=60)).timestamp())}, separators=(",", ":")).encode())
    signing = f"{header}.{payload}".encode()
    return f"{header}.{payload}.{_b64(hmac.new(settings.auth_secret.encode(), signing, hashlib.sha256).digest())}"


def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    try:
        header, payload, signature = authorization[7:].split(".")
        signing = f"{header}.{payload}".encode()
        expected = _b64(hmac.new(settings.auth_secret.encode(), signing, hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        data = json.loads(base64.urlsafe_b64decode(payload + "=="))
        if int(data["exp"]) < int(datetime.now(UTC).timestamp()):
            raise ValueError
        data["user_id"] = UUID(data["sub"])
        data["tenant_id"] = UUID(data["tenant_id"])
        return data
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def require_role(*roles: str):
    def dependency(user: dict = Depends(current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user
    return dependency
