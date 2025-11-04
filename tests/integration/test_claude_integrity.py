"""Integrity tests for the Claude adapter and service wiring.

These tests assert presence of endpoints and validate that the adapter can
call into the FastAPI app in-process using httpx's ASGI transport.
"""

from collections.abc import Iterator

import httpx
import pytest

from claude_chat_service.main import app
from claude_chat_service import main
from claude_chat_service.auth_deps import create_session_token
from claude_chat_adapter import ServiceClaudeChat
from claude_chat_impl import ClaudeChatImplementation, ClaudeAPIKeyRepository
from claude_chat_service_client import client as generated_client
from claude_chat_service_client.api.authentication import (
    upsert_claude_api_key_users_me_claude_key_post as upsert_key,
)


class _FakeReplyClient:
    def __init__(self, reply: str) -> None:
        self._reply = reply

    class _Messages:
        def __init__(self, outer: "_FakeReplyClient") -> None:
            self._outer = outer

        def create(self, **_: object):
            class _Resp:
                class _Part:
                    text = ""

                content = []

            r = _Resp()
            p = r._Part()  # type: ignore[attr-defined]
            p.text = self._outer._reply
            r.content = [p]
            return r

    @property
    def messages(self) -> "_FakeReplyClient._Messages":
        return _FakeReplyClient._Messages(self)


@pytest.fixture
def patched_app(tmp_path, mocker) -> Iterator[None]:
    """Patch main.impl and key repo so tests are isolated and deterministic."""
    original_repo = main.key_repository
    original_impl = main.impl

    repo = ClaudeAPIKeyRepository(str(tmp_path / "keys.db"))
    impl = ClaudeChatImplementation(key_repository=repo)
    main.key_repository = repo
    main.impl = impl
    mocker.patch.object(impl, "_create_client", return_value=_FakeReplyClient("Hello from Integrity"))
    try:
        yield None
    finally:
        main.key_repository = original_repo
        main.impl = original_impl


def test_openapi_contains_expected_paths() -> None:
    schema = app.openapi()
    paths = schema.get("paths", {})
    assert "/health" in paths
    assert "/chat" in paths and "post" in paths["/chat"]
    assert "/users/me/claude-key" in paths and "post" in paths["/users/me/claude-key"]


def test_adapter_calls_service_via_asgi_transport(patched_app) -> None:  # type: ignore[unused-argument]
    # Build an httpx client that routes to the ASGI app
    transport = httpx.ASGITransport(app=app)
    httpx_client = httpx.Client(base_url="http://testserver", transport=transport)

    # Use the generated client to upsert the key first
    gen = generated_client.Client(base_url="http://testserver").set_httpx_client(httpx_client)
    token = create_session_token("adapter-user@example.com")
    gen.cookies.update({"session_token": token})
    resp = upsert_key.sync_detailed(client=gen, body={"api_key": "sk-e2e"})
    assert resp.status_code == 204

    # Now exercise the adapter, wiring the same httpx client under the hood
    adapter = ServiceClaudeChat(base_url="http://testserver")
    adapter._client = adapter._client.set_httpx_client(httpx_client)  # type: ignore[attr-defined]
    adapter.set_session_token(token)

    msg = adapter.send_message(prompt="Hi", user_id="ignored@by.service")
    assert msg.content == "Hello from Integrity"
    assert msg.role.value == "assistant"

