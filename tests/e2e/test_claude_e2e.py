"""End-to-end tests for Claude chat service behavior.

These tests exercise the FastAPI app directly via TestClient and avoid
real network calls by stubbing the Anthropic client inside the implementation.
"""

from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from claude_chat_service import main
from claude_chat_service.main import app
from claude_chat_service.auth_deps import create_session_token
from claude_chat_impl import ClaudeChatImplementation, ClaudeAPIKeyRepository


@dataclass
class _FakeClaudeMessagePart:
    text: str


class _FakeClaudeClient:
    def __init__(self, reply_text: str) -> None:
        self._reply_text = reply_text

    class _Messages:
        def __init__(self, outer: "_FakeClaudeClient") -> None:
            self._outer = outer

        def create(self, **_: object):
            class _Resp:
                content = [_FakeClaudeMessagePart(text=self._outer._reply_text)]  # type: ignore[attr-defined]

            return _Resp()

    @property
    def messages(self) -> "_FakeClaudeClient._Messages":
        return _FakeClaudeClient._Messages(self)


@pytest.fixture
def service_client(tmp_path, mocker) -> Iterator[TestClient]:
    """Provide an isolated FastAPI TestClient with a temp key store and mocked Anthropic."""
    original_repo = main.key_repository
    original_impl = main.impl

    # Use a temp SQLite file for user keys
    repo = ClaudeAPIKeyRepository(str(tmp_path / "keys.db"))
    impl = ClaudeChatImplementation(key_repository=repo)

    # Patch the runtime globals used by the app
    main.key_repository = repo
    main.impl = impl

    # Stub Claude SDK creation to return a predictable fake
    mocker.patch.object(impl, "_create_client", return_value=_FakeClaudeClient("Hello from Claude E2E"))

    try:
        with TestClient(app) as client:
            yield client
    finally:
        main.key_repository = original_repo
        main.impl = original_impl


def test_full_flow_store_key_and_chat(service_client: TestClient) -> None:
    """User stores a key then chats successfully and gets mocked reply."""
    user_id = "user@example.com"
    token = create_session_token(user_id)

    # 1) Store Claude key
    resp = service_client.post(
        "/users/me/claude-key",
        json={"api_key": "sk-test-123"},
        cookies={"session_token": token},
    )
    assert resp.status_code == 204

    # 2) Chat
    chat = service_client.post(
        "/chat",
        json={"prompt": "Hi"},
        cookies={"session_token": token},
    )
    assert chat.status_code == 200
    body = chat.json()
    assert body == {"role": "assistant", "content": "Hello from Claude E2E"}


def test_chat_without_key_returns_400(service_client: TestClient) -> None:
    token = create_session_token("user2@example.com")
    chat = service_client.post(
        "/chat",
        json={"prompt": "Hi"},
        cookies={"session_token": token},
    )
    assert chat.status_code == 400
    assert "No Claude API key" in chat.json()["detail"]


def test_upsert_key_rejects_empty_value(service_client: TestClient) -> None:
    token = create_session_token("user3@example.com")
    resp = service_client.post(
        "/users/me/claude-key",
        json={"api_key": "  "},
        cookies={"session_token": token},
    )
    assert resp.status_code == 400
    assert "must not be empty" in resp.json()["detail"]

