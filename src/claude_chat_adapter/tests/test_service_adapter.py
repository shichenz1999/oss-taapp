"""Unit tests for the HTTP-based Claude chat adapter."""

from http import HTTPStatus

import pytest

from claude_chat_adapter import ServiceClaudeChat
from claude_chat_api import Message, MessageRole
from claude_chat_service_client.models.message import Message as ServiceMessage
from claude_chat_service_client.models.message_role import MessageRole as ServiceMessageRole
from claude_chat_service_client.types import Response


def _response(status: int, parsed=None, content: bytes | None = None) -> Response:
    return Response(
        status_code=HTTPStatus(status),
        content=content or b"",
        headers={},
        parsed=parsed,
    )


def test_send_message_success(mocker) -> None:
    """Adapter maps a successful service reply to the contract model."""
    # Arrange a generated-client Message as service response
    service_msg = ServiceMessage(role=ServiceMessageRole.ASSISTANT, content="Hello from service")

    mocker.patch(
        "claude_chat_service_client.api.chat.send_chat_message_chat_post.sync_detailed",
        return_value=_response(200, parsed=service_msg),
    )

    adapter = ServiceClaudeChat(base_url="http://127.0.0.1:8000", session_token="session-123")

    # Act
    result = adapter.send_message(prompt="Hello", user_id="user@example.com")

    # Assert
    assert isinstance(result, Message)
    assert result.role is MessageRole.ASSISTANT
    assert result.content == "Hello from service"


def test_send_message_unauthenticated_raises_permission_error(mocker) -> None:
    """401 responses are surfaced as PermissionError for callers."""
    mocker.patch(
        "claude_chat_service_client.api.chat.send_chat_message_chat_post.sync_detailed",
        return_value=_response(401, content=b'{"detail":"Not authenticated"}'),
    )

    adapter = ServiceClaudeChat(base_url="http://127.0.0.1:8000")

    with pytest.raises(PermissionError):
        adapter.send_message(prompt="Hello", user_id="user@example.com")


def test_send_message_bad_request_raises_runtime_error(mocker) -> None:
    """400 responses (e.g., missing user key) raise a RuntimeError."""
    mocker.patch(
        "claude_chat_service_client.api.chat.send_chat_message_chat_post.sync_detailed",
        return_value=_response(400, content=b'{"detail":"No key stored"}'),
    )

    adapter = ServiceClaudeChat(base_url="http://127.0.0.1:8000", session_token="x")

    with pytest.raises(RuntimeError):
        adapter.send_message(prompt="Hello", user_id="user@example.com")


def test_set_session_token_updates_cookie() -> None:
    """Cookies include the provided session token for subsequent calls."""
    adapter = ServiceClaudeChat(base_url="http://127.0.0.1:8000")
    adapter.set_session_token("abc123")
    # Access internal client to validate cookie state (acceptable for unit tests)
    assert adapter._client._cookies.get("session_token") == "abc123"
