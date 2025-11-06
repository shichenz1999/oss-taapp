"""Integration-style tests for the FastAPI AI chat service."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from ai_chat_api import Message, get_client
from ai_chat_service.main import app, auth_manager, get_current_user_id


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Provide a TestClient with automatic teardown."""
    with TestClient(app) as c:
        yield c


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_redirects_to_oauth_provider(client: TestClient, mocker: MockerFixture) -> None:
    mocker.patch.object(auth_manager, "get_authorization_url", return_value="https://accounts.example.com/auth")

    response = client.get("/auth/login", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://accounts.example.com/auth"


def test_auth_callback_sets_cookie_and_redirects(
    client: TestClient,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(auth_manager, "exchange_code_for_tokens", return_value={"access_token": "token-abc"})
    mocker.patch.object(auth_manager, "get_user_info", return_value={"email": "user@example.com"})
    mocker.patch("ai_chat_service.main.create_session_token", return_value="session-123")

    response = client.get("/auth/callback?code=test-code", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/docs"
    # TestClient stores cookies on the response object.
    assert response.cookies.get("session_token") == "session-123"


def test_chat_endpoint_requires_authentication(client: TestClient) -> None:
    response = client.post("/chat", json={"prompt": "Hello"})
    assert response.status_code == 401


def test_chat_endpoint_returns_ai_message(
    client: TestClient,
    mocker: MockerFixture,
) -> None:
    app.dependency_overrides[get_current_user_id] = lambda: "user@example.com"

    class _DummyClient:
        def send_message(self, prompt: str, user_id: str) -> Message:
            return DummyMessage(role="assistant", content="Mocked reply")

    app.dependency_overrides[get_client] = lambda: _DummyClient()

    try:
        response = client.post("/chat", json={"prompt": "Hi Claude"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"role": "assistant", "content": "Mocked reply"}

class DummyMessage(Message):
    def __init__(self, role: str, content: str) -> None:
        self._role = role
        self._content = content

    @property
    def role(self) -> str:
        return self._role

    @property
    def content(self) -> str:
        return self._content
