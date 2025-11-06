"""Tests for authentication dependency helpers."""

from __future__ import annotations

from typing import Iterable

import pytest
from fastapi import HTTPException, status
from jose import JWTError
from starlette.requests import Request

from ai_chat_service.auth_deps import create_session_token, get_current_user_id
from ai_chat_service.settings import settings


@pytest.fixture(autouse=True)
def _configure_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SESSION_SECRET_KEY", "test-secret", raising=False)
    monkeypatch.setattr(settings, "SESSION_ALGORITHM", "HS256", raising=False)


def _build_request(headers: Iterable[tuple[bytes, bytes]] | None = None) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": list(headers or []),
    }
    return Request(scope)


def test_get_current_user_id_requires_cookie() -> None:
    request = _build_request()

    with pytest.raises(HTTPException) as exc:
        get_current_user_id(request)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Please log in to send messages."


def test_get_current_user_id_handles_jwt_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    token = "fake-token"

    request = _build_request(headers=[(b"cookie", f"session_token={token}".encode())])
    def _raise(*args, **kwargs):
        raise JWTError("bad token")

    monkeypatch.setattr("ai_chat_service.auth_deps.jwt.decode", _raise)

    with pytest.raises(HTTPException) as exc:
        get_current_user_id(request)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Could not validate credentials"


def test_get_current_user_id_requires_subject(monkeypatch: pytest.MonkeyPatch) -> None:
    token = "fake-token"
    request = _build_request(headers=[(b"cookie", f"session_token={token}".encode())])
    monkeypatch.setattr("ai_chat_service.auth_deps.jwt.decode", lambda *args, **kwargs: {})

    with pytest.raises(HTTPException) as exc:
        get_current_user_id(request)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Could not validate credentials"


def test_get_current_user_id_success_round_trip() -> None:
    token = create_session_token("user@example.com")
    request = _build_request(headers=[(b"cookie", f"session_token={token}".encode())])

    user_id = get_current_user_id(request)

    assert user_id == "user@example.com"
