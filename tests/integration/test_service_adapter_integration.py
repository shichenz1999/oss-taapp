"""Integration test covering adapter -> service -> Gmail client chain."""

from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock, call

import anyio
import httpx
import pytest
from starlette.types import ASGIApp

import gmail_client_impl
import mail_client_api
import mail_client_service
import mail_client_adapter
from mail_client_adapter import ServiceMailClient

REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_SRC = REPO_ROOT / "src" / "mail_client_adapter" / "src"
if str(ADAPTER_SRC) not in sys.path:
    sys.path.insert(0, str(ADAPTER_SRC))

pytestmark = pytest.mark.integration


def _build_sync_transport(app: ASGIApp) -> httpx.MockTransport:
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


@pytest.mark.circleci
def test_mail_client_adapter_round_trip_through_service() -> None:
    """Service adapter should reach the FastAPI service and delegate to the Gmail client implementation."""
    sample_message = SimpleNamespace(
        id="msg-123",
        from_="from@example.com",
        to="to@example.com",
        date="2025-10-08",
        subject="Hello",
        body="hi there",
    )
    gmail_mock = Mock(spec=gmail_client_impl.GmailClient)
    gmail_mock.get_messages.return_value = [sample_message]
    gmail_mock.get_message.return_value = sample_message
    gmail_mock.mark_as_read.return_value = True
    gmail_mock.delete_message.return_value = True

    app = mail_client_service.app
    app.dependency_overrides[mail_client_service.get_mail_client] = lambda: gmail_mock
    mail_client_service._client_factory.cache_clear()

    base_url = "http://testserver"
    transport = _build_sync_transport(app)

    mail_client_adapter.register(base_url=base_url)
    adapter = mail_client_api.get_client(interactive=False)
    assert isinstance(adapter, ServiceMailClient)

    try:
        with httpx.Client(transport=transport, base_url=base_url) as http_client:
            adapter._client.set_httpx_client(http_client)

            messages = list(adapter.get_messages(max_results=1))
            fetched = adapter.get_message(sample_message.id)
            mark_result = adapter.mark_as_read(sample_message.id)
            delete_result = adapter.delete_message(sample_message.id)

        assert len(messages) == 1
        service_msg = messages[0]
        assert service_msg.id == sample_message.id
        assert service_msg.subject == sample_message.subject
        assert service_msg.body == sample_message.body
        assert fetched.id == sample_message.id
        assert fetched.body == sample_message.body
        assert mark_result is True
        assert delete_result is True

        gmail_mock.get_messages.assert_called_once_with(max_results=1)
        assert gmail_mock.get_message.call_args_list == [call(sample_message.id), call(sample_message.id)]
        gmail_mock.mark_as_read.assert_called_once_with(sample_message.id)
        gmail_mock.delete_message.assert_called_once_with(sample_message.id)
    finally:
        transport.close()
        app.dependency_overrides.pop(mail_client_service.get_mail_client, None)
        mail_client_service._client_factory.cache_clear()
        gmail_client_impl.register()
