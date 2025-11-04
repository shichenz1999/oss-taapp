"""Integration-style tests for the FastAPI Claude chat service."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from claude_chat_api import Message, MessageRole
from claude_chat_service import main
from claude_chat_service.main import app, get_current_user_id


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    """Provide a TestClient with automatic teardown and isolated storage."""
    original_repo = main.key_repository
    original_impl = main.impl
    main.key_repository = main.ClaudeAPIKeyRepository(str(tmp_path / "keys.db"))
    main.impl = main.ClaudeChatImplementation(key_repository=main.key_repository)
    try:
        with TestClient(app) as c:
            yield c
    finally:
        main.key_repository = original_repo
        main.impl = original_impl


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_redirects_to_oauth_provider(client: TestClient, mocker: MockerFixture) -> None:
    mocker.patch.object(
        main.auth_mgr,
        "get_authorization_url",
        return_value="https://accounts.example.com/auth",
    )

    response = client.get("/auth/login", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://accounts.example.com/auth"


def test_auth_callback_sets_cookie_and_redirects(
    client: TestClient,
    mocker: MockerFixture,
) -> None:
    mocker.patch.object(
        main.auth_mgr,
        "exchange_code_for_tokens",
        return_value={"access_token": "token-abc"},
    )
    mocker.patch.object(
        main.auth_mgr,
        "get_user_info",
        return_value={"email": "user@example.com"},
    )
    mocker.patch("claude_chat_service.main.create_session_token", return_value="session-123")

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
    mocker.patch.object(
        main.impl,
        "send_message",
        return_value=Message(role=MessageRole.ASSISTANT, content="Mocked reply"),
    )

    try:
        response = client.post("/chat", json={"prompt": "Hi Claude"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"role": "assistant", "content": "Mocked reply"}


def test_chat_endpoint_returns_400_when_key_missing(
    client: TestClient,
    mocker: MockerFixture,
) -> None:
    app.dependency_overrides[get_current_user_id] = lambda: "user@example.com"
    mocker.patch.object(
        main.impl,
        "send_message",
        side_effect=main.MissingClaudeAPIKeyError("No key stored"),
    )
    try:
        response = client.post("/chat", json={"prompt": "Hi Claude"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "No key stored"


def test_upsert_claude_api_key_persists_value(client: TestClient) -> None:
    user_id = "user@example.com"
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    try:
        response = client.post("/users/me/claude-key", json={"api_key": " sk-test "})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    stored = main.key_repository.get_api_key(user_id)
    assert stored == "sk-test"
