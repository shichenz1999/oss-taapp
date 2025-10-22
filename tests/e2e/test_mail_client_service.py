"""E2E tests that exercise the FastAPI service against the real Gmail backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from starlette.types import ASGIApp

import os
from pathlib import Path

import anyio
import httpx
import pytest

import gmail_client_impl
import mail_client_adapter
import mail_client_api
from mail_client_service.app import app, _client_factory, get_mail_client
from mail_client_adapter import ServiceMailClient

pytestmark = pytest.mark.e2e

BASE_URL = "http://testserver"


def _build_sync_transport(app: ASGIApp) -> httpx.MockTransport:
    """Return a synchronous transport that drives the ASGI app in-process."""
    asgi_transport = httpx.ASGITransport(app=app)

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


@pytest.fixture(scope="session")
def _gmail_credentials_ready() -> None:
    """Ensure we have either local credential files or Gmail env vars available."""
    workspace = Path(__file__).resolve().parents[2]
    credentials = workspace / "credentials.json"
    token = workspace / "token.json"

    have_files = credentials.exists() or token.exists()
    have_env = all(
        os.environ.get(var)
        for var in ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN")
    )

    if not (have_files or have_env):
        pytest.skip(
            "Need Gmail credentials via token.json/credentials.json or environment variables for live Gmail E2E",
        )


@pytest.fixture
def service_mail_client(_gmail_credentials_ready: None) -> Iterator[ServiceMailClient]:
    """Create a service-backed client that talks to the FastAPI app in-process."""
    _client_factory.cache_clear()

    real_client = mail_client_api.get_client(interactive=False)
    app.dependency_overrides[get_mail_client] = lambda: real_client

    transport = _build_sync_transport(app)
    http_client = httpx.Client(transport=transport, base_url=BASE_URL)

    mail_client_adapter.register(base_url=BASE_URL)
    client = mail_client_api.get_client(interactive=False)
    assert isinstance(client, ServiceMailClient)
    client._client.set_httpx_client(http_client)

    try:
        yield client
    finally:
        http_client.close()
        app.dependency_overrides.pop(get_mail_client, None)
        _client_factory.cache_clear()
        gmail_client_impl.register()


@pytest.mark.circleci
def test_service_roundtrip(service_mail_client: ServiceMailClient) -> None:
    messages = list(service_mail_client.get_messages(max_results=1))
    assert messages, "Expected at least one message from live Gmail API"

    first = messages[0]
    detailed = service_mail_client.get_message(first.id)

    assert detailed.id == first.id
    assert detailed.subject is not None
