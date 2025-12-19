"""Schemas for AI structured output."""
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field

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