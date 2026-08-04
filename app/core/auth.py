from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class UserStore:
    def __init__(self) -> None:
        self._users: dict[str, dict[str, Any]] = {
            "admin": {
                "username": "admin",
                "hashed_password": pwd_context.hash("admin"),
                "role": "admin",
            }
        }

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        user = self._users.get(username)
        if not user:
            return None
        if not pwd_context.verify(password, user["hashed_password"]):
            return None
        return user


user_store = UserStore()


def create_access_token(subject: str, expires_in_minutes: int = 60) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expires_in_minutes),
    }
    return jwt.encode(payload, settings.api_secret_key, algorithm="HS256")


def create_refresh_token(subject: str, expires_in_minutes: int = 60 * 24 * 7) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(minutes=expires_in_minutes),
    }
    return jwt.encode(payload, settings.api_secret_key, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.api_secret_key, algorithms=["HS256"])
    if payload.get("sub") is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return payload


def require_api_key(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> None:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    if payload.get("type") == "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not allowed")
