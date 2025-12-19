"""End-to-end flow test for smart_chat_bot (chat -> AI -> ticket -> reply)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from smart_chat_bot import main
from smart_chat_bot.schemas import BotAction, TicketIntent
from ticket_api.shared_interface import TicketStatus


class _DummyTicket:
    def __init__(self, title: str, status: TicketStatus) -> None:
        self.id = "42"
        self.title = title
        self.status = status
        self.assignee = None


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


@pytest.mark.asyncio
async def test_full_flow_create_ticket(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate chat -> AI intent -> ticket creation -> chat reply."""

    sent_messages: list[str] = []

    async def fake_fetch_recent_messages(_client: object, channel_id: str, limit: int) -> list[_DummyMessage]:
        return [_DummyMessage("m1", channel_id, "user1", "please open a ticket")]

    async def fake_send_message(_client: object, _channel_id: str, content: str) -> bool:
        sent_messages.append(content)
        return True

    async def fake_generate_bot_action(_ai: object, user_input: str) -> BotAction:
        assert user_input == "please open a ticket"
        return BotAction(
            intent=TicketIntent.CREATE_TICKET,
            params={"title": "Hello", "description": "desc", "priority": "high", "assignee": None},
        )

    class _StubTicketService:
        def create_ticket(self, title: str, description: str, assignee: str | None = None) -> _DummyTicket:
            return _DummyTicket(title, TicketStatus.OPEN)

    monkeypatch.setattr(main, "fetch_recent_messages", fake_fetch_recent_messages)
    monkeypatch.setattr(main, "send_message", fake_send_message)
    monkeypatch.setattr(main, "generate_bot_action", fake_generate_bot_action)
    monkeypatch.setattr(main, "ticket_service", _StubTicketService())

    last_seen: dict[str, str] = {}
    await main._handle_channel(client=object(), ai=object(), channel_id="C1", last_seen=last_seen)

    assert last_seen.get("C1") == "m1"
    assert sent_messages, "Expected a reply to be sent"
    assert "Ticket Created" in sent_messages[0]
