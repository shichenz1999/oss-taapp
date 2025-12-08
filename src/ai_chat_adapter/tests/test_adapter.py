from __future__ import annotations

from http import HTTPStatus
from typing import Any
from unittest.mock import Mock

import pytest

from ai_chat_adapter.adapter import AiChatServiceAdapter
from ai_chat_api import AIStructuredResponse


class DummyResponse:
    def __init__(self, status_code: int, payload: Any, content: bytes | None = None) -> None:
        self.status_code = status_code
        self._payload = payload
        self.content = content if content is not None else b""

    def json(self) -> Any:
        return self._payload


def test_generate_response_success() -> None:
    """Adapter should translate request/response and surface the structured response."""
    mock_client = Mock(name="service_client")
    httpx_client = Mock(name="httpx_client")
    mock_client.get_httpx_client.return_value = httpx_client
    http_response = DummyResponse(
        status_code=HTTPStatus.OK,
        payload={"intent": "create_ticket", "message": "Ticket created", "parameters": {"title": "hello user"}},
    )
    httpx_client.request.return_value = http_response

    adapter = AiChatServiceAdapter(client=mock_client)
    result = adapter.generate_response(
        user_input="hello world",
        system_prompt="act as assistant",
        response_schema={"type": "object"},
    )

    assert isinstance(result, AIStructuredResponse)
    assert result.intent == "create_ticket"
    assert result.message == "Ticket created"
    assert result.parameters["title"] == "hello user"
    httpx_client.request.assert_called_once()
    args, kwargs = httpx_client.request.call_args
    assert args[0] == "post"
    assert args[1] == "/chat"
    assert kwargs["json"]["user_input"] == "hello world"
    assert kwargs["json"]["system_prompt"] == "act as assistant"
    assert kwargs["json"]["response_schema"] == {"type": "object"}


def test_generate_response_raises_on_http_error() -> None:
    mock_client = Mock(name="service_client")
    httpx_client = Mock(name="httpx_client")
    mock_client.get_httpx_client.return_value = httpx_client
    httpx_client.request.return_value = DummyResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, payload={})

    adapter = AiChatServiceAdapter(client=mock_client)

    with pytest.raises(RuntimeError):
        adapter.generate_response(user_input="hello world", system_prompt="assist")


def test_generate_response_raises_on_invalid_payload() -> None:
    mock_client = Mock(name="service_client")
    httpx_client = Mock(name="httpx_client")
    mock_client.get_httpx_client.return_value = httpx_client
    httpx_client.request.return_value = DummyResponse(status_code=HTTPStatus.OK, payload={"unexpected": True})

    adapter = AiChatServiceAdapter(client=mock_client)

    with pytest.raises(TypeError):
        adapter.generate_response(user_input="hello world", system_prompt="assist")
