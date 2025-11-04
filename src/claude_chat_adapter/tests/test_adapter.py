import types
from typing import Any

import pytest

from claude_chat_api import Message, MessageRole


class _DummyHttpxResp:
    def __init__(self, status_code: int, payload: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = str(self._payload)

    def json(self) -> dict[str, Any]:
        return dict(self._payload)


def test_adapter_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter returns a typed Message on 200 responses."""
    # Lazy import to avoid import-time errors if the generated client isn't present
    from claude_chat_adapter.adapter import ServiceClaudeChat

    class _DummyClient:
        def __init__(self) -> None:
            self.cookies: dict[str, str] = {}
            self._httpx = types.SimpleNamespace(post=lambda url, json: _DummyHttpxResp(200, {"content": "hi"}))

        def with_cookies(self, cookies: dict[str, str]) -> "_DummyClient":
            self.cookies.update(cookies)
            return self

        def get_httpx_client(self):
            return self._httpx

    adapter = ServiceClaudeChat(base_url="http://test", session_token="token", client=_DummyClient())
    result = adapter.send_message(prompt="hello", user_id="user@example.com")

    assert isinstance(result, Message)
    assert result.role == MessageRole.ASSISTANT
    assert result.content == "hi"


def test_adapter_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    """Adapter raises PermissionError on 401."""
    from claude_chat_adapter.adapter import ServiceClaudeChat

    class _DummyClient:
        def __init__(self) -> None:
            self._httpx = types.SimpleNamespace(post=lambda url, json: _DummyHttpxResp(401, {"detail": "nope"}))

        def with_cookies(self, cookies):
            return self

        def get_httpx_client(self):
            return self._httpx

    adapter = ServiceClaudeChat(base_url="http://test", session_token="token", client=_DummyClient())

    with pytest.raises(PermissionError):
        adapter.send_message(prompt="hello", user_id="user@example.com")
