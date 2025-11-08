from http import HTTPStatus
from unittest.mock import Mock

import pytest

from ai_chat_adapter.adapter import AiChatServiceAdapter
from ai_chat_service_api_client.fast_api_client.models.chat_response import ChatResponse
from ai_chat_service_api_client.fast_api_client.models.http_validation_error import HTTPValidationError
from ai_chat_service_api_client.fast_api_client.types import Response


def test_send_message_success(monkeypatch) -> None:
    """Adapter should translate request/response and surface the abstract message."""
    mock_client = Mock(name="service_client")
    captured: dict[str, object] = {}
    service_response = ChatResponse(role="assistant", content="hello user")
    mock_message = Mock(name="abstract_message")

    def fake_sync_detailed(*, client, body):
        captured["client"] = client
        captured["body"] = body
        return Response(
            status_code=HTTPStatus.OK,
            content=b'{"role":"assistant","content":"hello user"}',
            headers={},
            parsed=service_response,
        )

    def fake_get_message(role: str, content: str):
        captured["role"] = role
        captured["content"] = content
        return mock_message

    monkeypatch.setattr(
        "ai_chat_adapter.adapter.send_chat_message_chat_post.sync_detailed",
        fake_sync_detailed,
    )
    monkeypatch.setattr("ai_chat_adapter.adapter.ai_chat_api.get_message", fake_get_message)

    adapter = AiChatServiceAdapter(client=mock_client)
    result = adapter.send_message(prompt="hello world", user_id="user-123")

    assert result is mock_message
    assert captured["client"] is mock_client
    assert captured["body"].prompt == "hello world"
    assert captured["role"] == "assistant"
    assert captured["content"] == "hello user"


def test_send_message_raises_on_http_error(monkeypatch) -> None:
    mock_client = Mock(name="service_client")

    def _http_error(*, client, body):
        _ = (client, body)
        return Response(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content=b"boom",
            headers={},
            parsed=None,
        )

    monkeypatch.setattr(
        "ai_chat_adapter.adapter.send_chat_message_chat_post.sync_detailed",
        _http_error,
    )

    adapter = AiChatServiceAdapter(client=mock_client)

    with pytest.raises(RuntimeError):
        adapter.send_message(prompt="hello world", user_id="user-123")


def test_send_message_raises_on_validation_error(monkeypatch) -> None:
    mock_client = Mock(name="service_client")

    def _validation_error(*, client, body):
        _ = (client, body)
        return Response(
            status_code=HTTPStatus.OK,
            content=b"validation failed",
            headers={},
            parsed=HTTPValidationError(),
        )

    monkeypatch.setattr(
        "ai_chat_adapter.adapter.send_chat_message_chat_post.sync_detailed",
        _validation_error,
    )

    adapter = AiChatServiceAdapter(client=mock_client)

    with pytest.raises(TypeError):
        adapter.send_message(prompt="hello world", user_id="user-123")
