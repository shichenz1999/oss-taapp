"""Integration test for smart_chat_bot with the real ticket implementation."""

from __future__ import annotations

import re
from typing import Any

import httpx
import pytest
import respx
from ai_chat_api import AIInterface
from chat_client_api import ChatInterface
from smart_chat_bot import main
from ticket_api.adapter import StandardizedTicketAdapter
from ticket_impl import TicketImpl
from ticket_impl.config import settings


class _DummyMessage:
    """Minimal Message implementation for testing."""

    def __init__(self, msg_id: str, channel_id: str, sender_id: str, content: str) -> None:
        self._id = msg_id
        self._channel_id = channel_id
        self._sender_id = sender_id
        self._content = content
        self._raw_data: dict[str, Any] = {"author": {"bot": False}}

    @property
    def id(self) -> str:
        return self._id

    @property
    def channel_id(self) -> str:
        return self._channel_id

    @property
    def sender_id(self) -> str:
        return self._sender_id

    @property
    def sender_name(self) -> str:
        return "tester"

    @property
    def content(self) -> str:
        return self._content

    @property
    def timestamp(self) -> str:
        return "now"

    @property
    def edited_timestamp(self) -> str | None:
        return None


class _StubChat(ChatInterface):
    def __init__(self, messages: list[_DummyMessage]) -> None:
        self._messages = messages
        self.sent: list[str] = []

    def get_message(self, channel_id: str, message_id: str) -> object:  # type: ignore[override]
        raise NotImplementedError

    def get_messages(self, channel_id: str, limit: int = 10) -> list[_DummyMessage]:  # type: ignore[override]
        return self._messages[:limit]

    def send_message(self, channel_id: str, content: str) -> bool:  # type: ignore[override]
        self.sent.append(content)
        return True

    def delete_message(self, channel_id: str, message_id: str) -> bool:  # type: ignore[override]
        raise NotImplementedError

    def get_channels(self) -> list[object]:  # type: ignore[override]
        raise NotImplementedError

    def get_channel(self, channel_id: str) -> object:  # type: ignore[override]
        raise NotImplementedError


class _StubAI(AIInterface):
    def generate_response(
        self,
        user_input: str,
        system_prompt: str | None = None,
        response_schema: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return {
            "intent": "create_ticket",
            "params": {
                "title": "Integration Bug",
                "description": "Integration failure",
                "priority": "high",
                "assignee": None,
            },
        }


@pytest.mark.asyncio
@pytest.mark.integration
@respx.mock
async def test_chatbot_integration_create_ticket(monkeypatch: pytest.MonkeyPatch) -> None:
    """Chat -> AI -> TicketImpl -> reply."""
    base = f"{settings.jira_api_base.rstrip('/')}/rest/api/3"
    respx.get(re.compile(f"{re.escape(base)}/user/search\\?.*")).mock(
        return_value=httpx.Response(200, json=[{"accountId": "acc-1", "displayName": "Reporter"}]),
    )
    respx.post(f"{base}/issue").mock(
        return_value=httpx.Response(201, json={"id": "10001", "key": "KAN-1"}),
    )
    respx.get(f"{base}/issue/KAN-1").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "10001",
                "key": "KAN-1",
                "fields": {
                    "summary": "Integration Bug",
                    "status": {"name": "Open"},
                    "priority": {"name": "Medium"},
                    "description": "Integration failure",
                    "assignee": None,
                    "reporter": {"displayName": "Reporter"},
                },
            },
        ),
    )

    ticket_service = StandardizedTicketAdapter(
        TicketImpl(user_id="u1", project_key="KAN"),
        reporter="u1",
    )
    monkeypatch.setattr(main, "ticket_service", ticket_service)

    message = _DummyMessage("m1", "C1", "user1", "please open a ticket")
    chat = _StubChat([message])
    last_seen: dict[str, str] = {}

    await main._handle_channel(client=chat, ai=_StubAI(), channel_id="C1", last_seen=last_seen)

    assert last_seen.get("C1") == "m1"
    assert chat.sent
    assert "Ticket Created" in chat.sent[0]
