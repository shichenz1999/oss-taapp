"""Schemas for AI structured output."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from ticket_api import TicketStatus


class Ticket(BaseModel):
    """Simple ticket shape that maps to tickets_api expectations."""

    title: str
    description: str
    status: TicketStatus | None = None
    assignee: str | None = None


class TicketIntent(str, Enum):
    CREATE_TICKET = "create_ticket"
    GET_TICKET = "get_ticket"
    SEARCH_TICKETS = "search_tickets"
    UPDATE_TICKET = "update_ticket"
    DELETE_TICKET = "delete_ticket"
    CHAT = "chat"


class BotAction(BaseModel):
    """Structure for the AI's response."""

    intent: TicketIntent
    params: dict[str, Any] = Field(default_factory=dict)
