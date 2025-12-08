"""End-to-end tests that exercise the AI chat stack via the public api_chat_api interface."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

import anyio
import httpx
import pytest

if TYPE_CHECKING:
    from starlette.types import ASGIApp

import ai_chat_adapter
import ai_chat_api
from ai_chat_service.auth_deps import create_session_token
from ai_chat_service import app
from ai_chat_service_api_client.fast_api_client.client import Client as ServiceClient

pytestmark = pytest.mark.e2e


def _build_sync_transport(asgi_app: ASGIApp) -> httpx.MockTransport:
    """Wrap FastAPI app in a sync httpx transport."""
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


def test_ai_chat_stack_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    """Register the adapter and call through ai_chat_api to hit the FastAPI service."""
    transport = _build_sync_transport(app)
    base_url = "http://testserver"
    claude_response = SimpleNamespace(
        role="assistant",
        content=[SimpleNamespace(text='{"intent":"ticket.create","parameters":{"title":"E2E reply"}}')],
    )

    monkeypatch.setattr(
        "claude_chat_impl.claude_impl.claude_client.messages.create",
        lambda *_, **__: claude_response,
    )

    previous_factory = ai_chat_api.get_ai_interface

    try:
        with httpx.Client(transport=transport, base_url=base_url) as http_client:
            http_client.cookies.set("session_token", create_session_token("user@example.com"))

            def _client_factory() -> ServiceClient:
                client = ServiceClient(base_url=base_url)
                client.set_httpx_client(http_client)
                return client

            ai_chat_adapter.register(client_factory=_client_factory)

            client = ai_chat_api.get_ai_interface()
            message = client.generate_response(
                user_input="Create a ticket",
                system_prompt="You are a helpful assistant",
                response_schema={"type": "object"},
            )

        assert message.intent == "ticket.create"
        assert message.parameters["title"] == "E2E reply"
    finally:
        ai_chat_api.get_ai_interface = previous_factory
        transport.close()
