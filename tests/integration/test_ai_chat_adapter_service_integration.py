"""Integration test covering ai_chat_adapter -> ai_chat_service path."""

from __future__ import annotations

from typing import Any

import anyio
import httpx
import pytest
from starlette.types import ASGIApp

import ai_chat_adapter
import ai_chat_api
from ai_chat_adapter.adapter import AiChatAdapter
from ai_chat_api import AIInterface
from ai_chat_service import main as ai_chat_service_main
from ai_chat_service.main import app

pytestmark = [pytest.mark.integration, pytest.mark.circleci]

BASE_URL = "http://testserver"


class _StubAI(AIInterface):
    """Simple AI stub that records calls."""

    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def generate_response(
        self,
        user_input: str,
        system_prompt: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.calls.append(
            {
                "user_input": user_input,
                "system_prompt": system_prompt,
                "response_schema": response_schema,
            }
        )
        return self.response


def _build_sync_transport(asgi_app: ASGIApp) -> httpx.MockTransport:
    asgi_transport = httpx.ASGITransport(app=asgi_app)

    def _handler(request: httpx.Request) -> httpx.Response:
        async def _invoke() -> httpx.Response:
            response = await asgi_transport.handle_async_request(request)
            content = await response.aread()
            return httpx.Response(
                status_code=response.status_code,
                headers=response.headers,
                content=content,
                request=request,
                extensions=response.extensions,
            )

        return anyio.run(_invoke)

    return httpx.MockTransport(_handler)


def test_ai_chat_adapter_round_trip_through_service() -> None:
    """Adapter should call the FastAPI service and surface the stubbed AI response."""
    expected = {
        "tool_calls": [
            {
                "id": "call-1",
                "type": "function",
                "function": {
                    "name": "delete_ticket",
                    "arguments": {"ticket_id": "12345", "confirm": True},
                },
            }
        ]
    }
    response_schema = {
        "type": "object",
        "properties": {
            "tool_calls": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string", "enum": ["function"]},
                        "function": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "arguments": {
                                    "type": "object",
                                    "properties": {
                                        "ticket_id": {"type": "string"},
                                        "confirm": {"type": "boolean"},
                                    },
                                    "required": ["ticket_id", "confirm"],
                                    "additionalProperties": False,
                                },
                            },
                            "required": ["name", "arguments"],
                            "additionalProperties": False,
                        },
                    },
                    "required": ["id", "type", "function"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["tool_calls"],
        "additionalProperties": False,
    }

    stub_ai = _StubAI(expected)
    app.dependency_overrides[ai_chat_service_main.get_ai_interface] = lambda: stub_ai
    transport = _build_sync_transport(app)
    original_factory = ai_chat_api.get_ai_interface

    try:
        ai_chat_adapter.register(base_url=BASE_URL)
        adapter = ai_chat_api.get_ai_interface()
        assert isinstance(adapter, AiChatAdapter)

        with httpx.Client(transport=transport, base_url=BASE_URL) as http_client:
            adapter._client.set_httpx_client(http_client)
            result = adapter.generate_response(
                user_input="Delete ticket 12345",
                system_prompt="Return a tool call for delete_ticket.",
                response_schema=response_schema,
            )

        assert result == expected
        assert stub_ai.calls == [
            {
                "user_input": "Delete ticket 12345",
                "system_prompt": "Return a tool call for delete_ticket.",
                "response_schema": response_schema,
            }
        ]
    finally:
        app.dependency_overrides.pop(ai_chat_service_main.get_ai_interface, None)
        transport.close()
        ai_chat_api.get_ai_interface = original_factory
