"""Integration-style tests for the FastAPI AI chat service."""

from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from ai_chat_api import AIInterface, AIStructuredResponse, get_ai_interface
from ai_chat_service.auth_deps import create_session_token
from ai_chat_service import app, auth_manager, get_current_user_id


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Provide a TestClient with automatic teardown."""
    with TestClient(app) as c:
        yield c


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_landing_redirects_to_docs(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 308
    assert response.headers["location"] == "/docs"


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


def test_auth_callback_with_error_returns_400(client: TestClient) -> None:
    response = client.get("/auth/callback?error=access_denied", follow_redirects=False)

    assert response.status_code == 400
    assert response.json() == {"detail": "OAuth Error: access_denied"}


def test_auth_callback_missing_code_returns_400(client: TestClient) -> None:
    response = client.get("/auth/callback", follow_redirects=False)

    assert response.status_code == 400
    assert response.json() == {"detail": "Missing 'code' query parameter"}


def test_auth_callback_missing_access_token_returns_500(client: TestClient, mocker: MockerFixture) -> None:
    mocker.patch.object(auth_manager, "exchange_code_for_tokens", return_value={})

    response = client.get("/auth/callback?code=xyz", follow_redirects=False)

    assert response.status_code == 500
    assert response.json() == {"detail": "Could not retrieve access token"}


def test_auth_callback_missing_user_identifier_returns_500(client: TestClient, mocker: MockerFixture) -> None:
    mocker.patch.object(auth_manager, "exchange_code_for_tokens", return_value={"access_token": "token-abc"})
    mocker.patch.object(auth_manager, "get_user_info", return_value={})

    response = client.get("/auth/callback?code=xyz", follow_redirects=False)

    assert response.status_code == 500
    assert response.json() == {"detail": "Could not retrieve user identifier"}


def test_logout_clears_session_cookie(client: TestClient) -> None:
    response = client.get("/auth/logout", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/docs"
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "session_token=" in set_cookie_header
    assert "Max-Age=0" in set_cookie_header


def test_chat_endpoint_requires_authentication(client: TestClient) -> None:
    response = client.post("/chat", json={"user_input": "Hello", "system_prompt": "assist"})
    assert response.status_code == 401


def test_chat_endpoint_with_valid_token(client: TestClient, mocker: MockerFixture) -> None:
    mocker.patch(
        "claude_chat_impl.claude_impl.claude_client.messages.create",
        return_value=SimpleNamespace(
            role="assistant",
            content=[SimpleNamespace(text='{"intent":"ticket.create","parameters":{"title":"Patched reply"}}')],
        ),
    )
    token = create_session_token("user@example.com")

    client.cookies.set("session_token", token)
    try:
        response = client.post(
            "/chat",
            json={
                "user_input": "Create a ticket for me",
                "system_prompt": "You are a support bot",
                "response_schema": {"type": "object"},
            },
        )
    finally:
        client.cookies.clear()

    assert response.status_code == 200
    assert response.json() == {"intent": "ticket.create", "parameters": {"title": "Patched reply"}}


def test_chat_endpoint_returns_ai_message(
    client: TestClient,
    mocker: MockerFixture,
) -> None:
    app.dependency_overrides[get_current_user_id] = lambda: "user@example.com"
    mocker.patch(
        "claude_chat_impl.claude_impl.claude_client.messages.create",
        return_value=SimpleNamespace(
            role="assistant",
            content=[SimpleNamespace(text="Mocked reply")],
        ),
    )

    class _DummyClient(AIInterface):
        def generate_response(
            self,
            user_input: str,
            system_prompt: str,
            response_schema: dict[str, object] | None = None,
        ) -> str | AIStructuredResponse:
            _ = (user_input, system_prompt, response_schema)
            return AIStructuredResponse(intent="message", parameters={"response": "Mocked reply"})

    app.dependency_overrides[get_ai_interface] = lambda: _DummyClient()

    try:
        response = client.post(
            "/chat",
            json={
                "user_input": "Hi Claude",
                "system_prompt": "You are a helpful assistant",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"intent": "message", "parameters": {"response": "Mocked reply"}}
