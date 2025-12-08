"""Integration tests for AiChatServiceAdapter running against the FastAPI service."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import anyio
import httpx
import pytest

if TYPE_CHECKING:
    from starlette.types import ASGIApp

from ai_chat_adapter.adapter import AiChatServiceAdapter
from ai_chat_service.auth_deps import create_session_token
from ai_chat_service import app
from ai_chat_service_api_client.fast_api_client.client import Client as ServiceClient

pytestmark = pytest.mark.integration


def _build_sync_transport(asgi_app: ASGIApp) -> httpx.MockTransport:
    """Wrap an ASGI app in a synchronous transport for httpx.Client."""
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


def _build_adapter(http_client: httpx.Client, base_url: str) -> AiChatServiceAdapter:
    client = ServiceClient(base_url=base_url)
    client.set_httpx_client(http_client)
    return AiChatServiceAdapter(client=client)


@pytest.mark.circleci
def test_ai_chat_adapter_round_trip_through_service(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter should hit the FastAPI service and return the Claude-generated reply."""
    transport = _build_sync_transport(app)
    base_url = "http://testserver"
    claude_response = SimpleNamespace(
        role="assistant",
        content=[
            SimpleNamespace(
                text='{"intent":"create_ticket","message":"Ticket created","parameters":{"title":"Integration reply"}}',
            )
        ],
    )

    monkeypatch.setattr(
        "claude_chat_impl.claude_impl.claude_client.messages.create",
        lambda *_, **__: claude_response,
    )

    try:
        with httpx.Client(transport=transport, base_url=base_url) as http_client:
            token = create_session_token("user@example.com")
            http_client.cookies.set("session_token", token)
            adapter = _build_adapter(http_client, base_url)

            message = adapter.generate_response(
                user_input="Create a ticket",
                system_prompt="You are a helpful assistant",
                response_schema={"type": "object"},
            )

        assert message.intent == "create_ticket"
        assert message.message == "Ticket created"
        assert message.parameters["title"] == "Integration reply"
    finally:
        transport.close()


def test_ai_chat_adapter_requires_session_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Requests without a session token should surface the FastAPI 401 response."""
    transport = _build_sync_transport(app)
    base_url = "http://testserver"

    try:
        with httpx.Client(transport=transport, base_url=base_url) as http_client:
            adapter = _build_adapter(http_client, base_url)

            with pytest.raises(RuntimeError) as exc:
                adapter.generate_response(
                    user_input="Hi",
                    system_prompt="You are a helpful assistant",
                    response_schema={"type": "object"},
                )

        assert "401" in str(exc.value)
    finally:
        transport.close()
