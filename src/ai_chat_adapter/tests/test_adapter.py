from __future__ import annotations

from http import HTTPStatus
from typing import Any, TYPE_CHECKING, cast
from unittest.mock import Mock

import pytest

from ai_chat_adapter.adapter import AiChatAdapter
from ai_chat_service_client.models.chat_response import ChatResponse
from ai_chat_service_client.models.http_validation_error import HTTPValidationError
from ai_chat_service_client.types import Response

if TYPE_CHECKING:
    from ai_chat_service_client.models.chat_request import ChatRequest as ServiceChatRequest


def test_generate_response_success(monkeypatch) -> None:
    """Adapter should translate request/response and surface the service payload."""
    mock_client = Mock(name="service_client")
    captured: dict[str, Any] = {}
    service_response = ChatResponse(response={"text": "hello user"})

    def fake_sync_detailed(*, client, body):
        captured["client"] = client
        captured["body"] = body
        return Response(
            status_code=HTTPStatus.OK,
            content=b'{"response":{"text":"hello user"}}',
            headers={},
            parsed=service_response,
        )

    monkeypatch.setattr(
        "ai_chat_adapter.adapter.send_chat_message_chat_post.sync_detailed",
        fake_sync_detailed,
    )

    adapter = AiChatAdapter(client=mock_client)
    result = adapter.generate_response(
        user_input="hello world",
        system_prompt="system",
        response_schema={"type": "object"},
    )

    assert result == {"text": "hello user"}
    assert captured["client"] is mock_client
    body = cast("ServiceChatRequest", captured["body"])
    assert body.user_input == "hello world"
    assert body.system_prompt == "system"
    assert body.response_schema == {"type": "object"}


def test_generate_response_raises_on_http_error(monkeypatch) -> None:
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

    adapter = AiChatAdapter(client=mock_client)

    with pytest.raises(RuntimeError):
        adapter.generate_response(user_input="hello world")


def test_generate_response_raises_on_validation_error(monkeypatch) -> None:
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

    adapter = AiChatAdapter(client=mock_client)

    with pytest.raises(TypeError):
        adapter.generate_response(user_input="hello world")
