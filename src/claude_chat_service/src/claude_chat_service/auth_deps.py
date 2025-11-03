"""Authentication helpers used by the Claude chat service."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from claude_chat_impl.settings import settings
from fastapi import HTTPException, Request, status
from jose import JWTError, jwt  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from collections.abc import Mapping


def get_current_user_id(request: Request) -> str:
    """Validate the session cookie and return the authenticated user id."""
    token = request.cookies.get("session_token")
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (missing session cookie)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SESSION_SECRET_KEY, algorithms=[settings.SESSION_ALGORITHM])
    except JWTError as exc:
        raise credentials_exception from exc

    if not isinstance(payload, dict):
        raise credentials_exception

    payload_dict = cast("Mapping[str, object]", payload)
    user_id_raw = payload_dict.get("sub")
    if not isinstance(user_id_raw, str):
        raise credentials_exception

    return user_id_raw


def create_session_token(user_id: str) -> str:
    """Create a signed JWT session token for the given user id."""
    to_encode = {"sub": user_id}
    token = jwt.encode(
        to_encode,
        settings.SESSION_SECRET_KEY,
        algorithm=settings.SESSION_ALGORITHM,
    )
    return cast("str", token)
