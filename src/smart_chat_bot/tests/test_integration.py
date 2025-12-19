"""Integration-style tests for smart_chat_bot flows."""

from __future__ import annotations

import pytest
from collections import deque

from ai_chat_api import AIInterface
from chat_client_api.client import ChatInterface
from smart_chat_bot import main
from smart_chat_bot.schemas import BotAction, TicketIntent
from ticket_api.shared_interface import TicketStatus


class _DummyMessage:
    """Minimal Message implementation for tests."""

    def __init__(self, msg_id: str, channel_id: str, sender_id: str, content: str) -> None:
        self._id = msg_id
        self._channel_id = channel_id
        self._sender_id = sender_id
        self._content = content
        self._raw_data: dict[str, object] = {"author": {"bot": False}}

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
    def get_message(self, channel_id: str, message_id: str) -> object:  # type: ignore[override]
        raise NotImplementedError

    def get_messages(self, channel_id: str, limit: int = 10) -> list[object]:  # type: ignore[override]
        raise NotImplementedError

    def send_message(self, channel_id: str, content: str) -> bool:  # type: ignore[override]
        raise NotImplementedError

    def delete_message(self, channel_id: str, message_id: str) -> bool:  # type: ignore[override]
        raise NotImplementedError

    def get_channels(self) -> list[object]:  # type: ignore[override]
        raise NotImplementedError

    def get_channel(self, channel_id: str) -> object:  # type: ignore[override]
        raise NotImplementedError


class _StubAI(AIInterface):
    def __init__(self, action: BotAction) -> None:
        self.action = action

    def generate_response(
        self,
        user_input: str,
        system_prompt: str | None = None,
        response_schema: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return {"intent": self.action.intent.value, "params": self.action.params}


class _StubTicketService:
    def __init__(self) -> None:
        self.created: list[tuple[str, str, str | None]] = []
        self.searched: list[tuple[str | None, TicketStatus | None]] = []
        self.updated: list[tuple[str, TicketStatus | None, str | None]] = []
        self.deleted: list[str] = []

    def create_ticket(self, title: str, description: str, assignee: str | None = None) -> object:
        self.created.append((title, description, assignee))
        return type("T", (), {"id": "99", "title": title, "status": TicketStatus.OPEN})

    def search_tickets(self, query: str | None = None, status: TicketStatus | None = None) -> list[object]:
        self.searched.append((query, status))
        return []

    def update_ticket(
        self, ticket_id: str, status: TicketStatus | None = None, title: str | None = None
    ) -> object:
        self.updated.append((ticket_id, status, title))
        return type("T", (), {"id": ticket_id, "title": title or "t", "status": status or TicketStatus.OPEN})

    def delete_ticket(self, ticket_id: str) -> bool:
        self.deleted.append(ticket_id)
        return True


@pytest.mark.asyncio
async def test_ai_chat_flow_sends_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    """AI chat intent should yield a chat reply sent via chat client."""
    sent: list[str] = []

    async def fake_fetch_recent_messages(_client: object, channel_id: str, limit: int) -> list[_DummyMessage]:
        return [_DummyMessage("m1", channel_id, "user", "hello bot")]

    async def fake_send_message(_client: object, _channel_id: str, content: str) -> bool:
        sent.append(content)
        return True

    action = BotAction(intent=TicketIntent.CHAT, params={"message": "hi there"})

    async def fake_generate_bot_action(_ai: object, _msg: str) -> BotAction:
        return action

    monkeypatch.setattr(main, "fetch_recent_messages", fake_fetch_recent_messages)
    monkeypatch.setattr(main, "send_message", fake_send_message)
    monkeypatch.setattr(main, "generate_bot_action", fake_generate_bot_action)

    last_seen: dict[str, str] = {}
    await main._handle_channel(client=_StubChat(), ai=_StubAI(action), channel_id="C", last_seen=last_seen)

    assert sent == ["hi there"]
    assert last_seen.get("C") == "m1"


@pytest.mark.asyncio
async def test_chat_to_ticket_create_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ticket create intent should invoke ticket service and send a confirmation."""
    sent: list[str] = []
    ticket_service = _StubTicketService()

    async def fake_fetch_recent_messages(_client: object, channel_id: str, limit: int) -> list[_DummyMessage]:
        return [_DummyMessage("m2", channel_id, "user", "open a ticket")]

    async def fake_send_message(_client: object, _channel_id: str, content: str) -> bool:
        sent.append(content)
        return True

    action = BotAction(
        intent=TicketIntent.CREATE_TICKET,
        params={"title": "Hello", "description": "desc", "priority": "high", "assignee": None},
    )

    async def fake_generate_bot_action(_ai: object, _msg: str) -> BotAction:
        return action

    monkeypatch.setattr(main, "fetch_recent_messages", fake_fetch_recent_messages)
    monkeypatch.setattr(main, "send_message", fake_send_message)
    monkeypatch.setattr(main, "generate_bot_action", fake_generate_bot_action)
    monkeypatch.setattr(main, "ticket_service", ticket_service)

    last_seen: dict[str, str] = {}
    await main._handle_channel(client=_StubChat(), ai=_StubAI(action), channel_id="C2", last_seen=last_seen)

    assert ticket_service.created == [("Hello", "[HIGH] desc", None)]
    assert any("Ticket Created" in msg for msg in sent)
    assert last_seen.get("C2") == "m2"


@pytest.mark.asyncio
async def test_ticket_search_update_delete_intents(monkeypatch: pytest.MonkeyPatch) -> None:
    """Search, update, delete intents should hit ticket service and send replies."""
    sent: list[str] = []
    ticket_service = _StubTicketService()

    messages = deque(
        [
            _DummyMessage("m3a", "C3", "user", "search something"),
            _DummyMessage("m3b", "C3", "user", "update it"),
            _DummyMessage("m3c", "C3", "user", "delete it"),
        ]
    )

    async def fake_fetch_recent_messages(_client: object, channel_id: str, limit: int) -> list[_DummyMessage]:
        if messages:
            return [messages.popleft()]
        return []

    async def fake_send_message(_client: object, _channel_id: str, content: str) -> bool:
        sent.append(content)
        return True

    # Prepare a sequence of actions to simulate multiple intents
    actions = deque(
        [
            BotAction(intent=TicketIntent.SEARCH_TICKETS, params={"query": "something", "status": "open"}),
            BotAction(intent=TicketIntent.UPDATE_TICKET, params={"ticket_id": "77", "status": "open", "title": "New"}),
            BotAction(intent=TicketIntent.DELETE_TICKET, params={"ticket_id": "77"}),
        ]
    )

    async def fake_generate_bot_action(_ai: object, user_input: str) -> BotAction:
        return actions.popleft()

    monkeypatch.setattr(main, "fetch_recent_messages", fake_fetch_recent_messages)
    monkeypatch.setattr(main, "send_message", fake_send_message)
    monkeypatch.setattr(main, "generate_bot_action", fake_generate_bot_action)
    monkeypatch.setattr(main, "ticket_service", ticket_service)

    last_seen: dict[str, str] = {}
    dummy = BotAction(intent=TicketIntent.CHAT, params={"message": "hi"})
    ai_stub = _StubAI(dummy)
    # Run three times to consume all intents
    await main._handle_channel(client=_StubChat(), ai=ai_stub, channel_id="C3", last_seen=last_seen)
    await main._handle_channel(client=_StubChat(), ai=ai_stub, channel_id="C3", last_seen=last_seen)
    await main._handle_channel(client=_StubChat(), ai=ai_stub, channel_id="C3", last_seen=last_seen)

    assert ticket_service.searched == [("something", TicketStatus.OPEN)]
    assert ticket_service.updated == [("77", TicketStatus.OPEN, "New")]
    assert ticket_service.deleted == ["77"]
    assert len(sent) == 3
