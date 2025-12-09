"""E2E test for ai_chat_service using the generated client."""

from __future__ import annotations

from typing import Any

import anyio
import httpx
import pytest
from starlette.types import ASGIApp

import ai_chat_api
from ai_chat_api import AIInterface
from ai_chat_service import main as ai_chat_service_main
from ai_chat_service.main import app
from ai_chat_service_client.api.chat import send_chat_message_chat_post
from ai_chat_service_client.client import Client
from ai_chat_service_client.models.chat_request import ChatRequest
from ai_chat_service_client.models.chat_response import ChatResponse

pytestmark = [pytest.mark.e2e, pytest.mark.circleci]

BASE_URL = "http://testserver"


class _StubAI(AIInterface):
    """AI stub that records calls for assertions."""

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


def test_service_client_round_trip() -> None:
    """Generated client should reach the FastAPI service and surface structured responses."""
    expected = {
        "tool_calls": [
            {
                "id": "call-1",
                "type": "function",
                "function": {
                    "name": "delete_ticket",
                    "arguments": {"ticket_id": "98765", "confirm": False},
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
    http_client = httpx.Client(transport=transport, base_url=BASE_URL)
    client = Client(base_url=BASE_URL)
    client.set_httpx_client(http_client)
    original_factory = ai_chat_api.get_ai_interface

    try:
        response = send_chat_message_chat_post.sync_detailed(
            client=client,
            body=ChatRequest(
                user_input="Delete ticket 98765",
                system_prompt="Use delete_ticket tool.",
                response_schema=response_schema,
            ),
        )

        assert response.status_code == 200
        assert isinstance(response.parsed, ChatResponse)
        parsed_response = response.parsed.response
        if hasattr(parsed_response, "to_dict"):
            parsed_response = parsed_response.to_dict()
        assert parsed_response == expected
        assert stub_ai.calls == [
            {
                "user_input": "Delete ticket 98765",
                "system_prompt": "Use delete_ticket tool.",
                "response_schema": response_schema,
            }
        ]
    finally:
        app.dependency_overrides.pop(ai_chat_service_main.get_ai_interface, None)
        http_client.close()
        transport.close()
        ai_chat_api.get_ai_interface = original_factory
