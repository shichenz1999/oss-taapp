"""Tests for smart_chat_bot main logic."""

from __future__ import annotations

import asyncio

import pytest

from smart_chat_bot import main
from smart_chat_bot.schemas import BotAction, TicketIntent
from ticket_api.shared_interface import TicketStatus


class _DummyTicket:
    def __init__(self, title: str, status: TicketStatus, assignee: str | None) -> None:
        self.id = "1"
        self.title = title
        self.status = status
        self.assignee = assignee


class _StubTicketService:
    def __init__(self) -> None:
        self.last_create_args: tuple[str, str, str | None] | None = None

    def create_ticket(self, title: str, description: str, assignee: str | None = None) -> _DummyTicket:
        self.last_create_args = (title, description, assignee)
        return _DummyTicket(title, TicketStatus.OPEN, assignee)


class _FakeAI:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def generate_response(self, user_input: str, system_prompt: str | None, response_schema: dict | None) -> dict[str, object]:
        return self.payload


@pytest.mark.asyncio
async def test_generate_bot_action_parses_structured_dict() -> None:
    """AI dict output is parsed into a BotAction without fallback."""
    ai = _FakeAI({"intent": "chat", "params": {"message": "hi"}})

    action = await main.generate_bot_action(ai, "hello")

    assert action.intent is TicketIntent.CHAT
    assert action.params["message"] == "hi"


@pytest.mark.asyncio
async def test_execute_ticket_action_create_injects_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    """CREATE_TICKET intent calls ticket service and injects priority into description."""
    stub_service = _StubTicketService()
    monkeypatch.setattr(main, "ticket_service", stub_service)

    action = BotAction(
        intent=TicketIntent.CREATE_TICKET,
        params={
            "title": "Bug report",
            "description": "Something broken",
            "priority": "high",
            "assignee": "alice",
        },
    )

    reply = await main.execute_ticket_action(action)

    assert "Ticket Created" in reply
    assert stub_service.last_create_args is not None
    title, description, assignee = stub_service.last_create_args
    assert title == "Bug report"
    assert "[HIGH]" in description  # priority injection
    assert assignee == "alice"


@pytest.mark.asyncio
async def test_execute_ticket_action_get_ticket(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET_TICKET intent returns details or not-found."""
    class _StubService(_StubTicketService):
        def __init__(self, ticket: _DummyTicket | None) -> None:
            super().__init__()
            self.ticket = ticket

        def get_ticket(self, ticket_id: str) -> _DummyTicket | None:
            return self.ticket

    ticket = _DummyTicket("Hello", TicketStatus.OPEN, "bob")
    monkeypatch.setattr(main, "ticket_service", _StubService(ticket))

    action = BotAction(intent=TicketIntent.GET_TICKET, params={"ticket_id": "123"})
    reply = await main.execute_ticket_action(action)

    assert "Ticket 1" in reply


@pytest.mark.asyncio
async def test_execute_ticket_action_search(monkeypatch: pytest.MonkeyPatch) -> None:
    """SEARCH_TICKETS intent lists results or no tickets."""
    class _StubService(_StubTicketService):
        def search_tickets(
            self, query: str | None = None, status: TicketStatus | None = None
        ) -> list[_DummyTicket]:
            return [_DummyTicket("Found", TicketStatus.OPEN, None)] if query == "q" else []

    monkeypatch.setattr(main, "ticket_service", _StubService())

    action = BotAction(intent=TicketIntent.SEARCH_TICKETS, params={"query": "q", "status": "open"})
    reply = await main.execute_ticket_action(action)
    assert "Results" in reply

    action_empty = BotAction(intent=TicketIntent.SEARCH_TICKETS, params={"query": "none"})
    reply_empty = await main.execute_ticket_action(action_empty)
    assert "No tickets" in reply_empty


@pytest.mark.asyncio
async def test_execute_ticket_action_update(monkeypatch: pytest.MonkeyPatch) -> None:
    """UPDATE_TICKET intent updates and returns summary."""
    class _StubService(_StubTicketService):
        def update_ticket(
            self, ticket_id: str, status: TicketStatus | None = None, title: str | None = None
        ) -> _DummyTicket:
            return _DummyTicket(title or "t", status or TicketStatus.OPEN, None)

    monkeypatch.setattr(main, "ticket_service", _StubService())

    action = BotAction(
        intent=TicketIntent.UPDATE_TICKET,
        params={"ticket_id": "123", "status": "open", "title": "New"},
    )
    reply = await main.execute_ticket_action(action)
    assert "updated" in reply


@pytest.mark.asyncio
async def test_execute_ticket_action_delete(monkeypatch: pytest.MonkeyPatch) -> None:
    """DELETE_TICKET intent deletes and reports success."""
    class _StubService(_StubTicketService):
        def delete_ticket(self, ticket_id: str) -> bool:
            return ticket_id == "ok"

    monkeypatch.setattr(main, "ticket_service", _StubService())

    action = BotAction(intent=TicketIntent.DELETE_TICKET, params={"ticket_id": "ok"})
    reply = await main.execute_ticket_action(action)
    assert "deleted" in reply


@pytest.mark.asyncio
async def test_execute_ticket_action_chat() -> None:
    """CHAT intent returns message."""
    action = BotAction(intent=TicketIntent.CHAT, params={"message": "hi"})
    reply = await main.execute_ticket_action(action)
    assert reply == "hi"
