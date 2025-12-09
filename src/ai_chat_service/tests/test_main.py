"""Tests for the simplified AI chat FastAPI service."""

from typing import Any, Iterator

import pytest
from fastapi.testclient import TestClient

from ai_chat_api import AIInterface, get_ai_interface
from ai_chat_service import app


class _DummyInterface(AIInterface):
    """Test double that returns configurable values."""

    def __init__(self, response: str | dict[str, Any], *, raise_error: bool = False) -> None:
        self._response = response
        self._raise_error = raise_error

    def generate_response(
        self,
        user_input: str,
        system_prompt: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        if self._raise_error:
            raise ValueError("boom")
        return self._response


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_endpoint_returns_text_response(client: TestClient) -> None:
    app.dependency_overrides[get_ai_interface] = lambda: _DummyInterface("hello world")
    try:
        response = client.post("/chat", json={"user_input": "Hi"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"response": "hello world"}


def test_chat_endpoint_supports_structured_response(client: TestClient) -> None:
    payload = {
        "text": "Review complete.",
        "tools": [
            {"name": "list_tickets", "args": {}},
            {"name": "delete_ticket", "args": {"ticket_id": "A-102"}},
        ],
    }
    app.dependency_overrides[get_ai_interface] = lambda: _DummyInterface(payload)
    try:
        response = client.post(
            "/chat",
            json={
                "user_input": "Plan tomorrow",
                "response_schema": {"type": "object"},
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"response": payload}


def test_chat_endpoint_returns_502_on_value_error(client: TestClient) -> None:
    app.dependency_overrides[get_ai_interface] = lambda: _DummyInterface("ignored", raise_error=True)
    try:
        response = client.post("/chat", json={"user_input": "Hi"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json()["detail"].startswith("AI response could not be parsed")
