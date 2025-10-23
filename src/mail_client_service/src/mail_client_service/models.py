"""Pydantic models used by the mail client service."""

from pydantic import BaseModel


class MessageSummary(BaseModel):
    """Minimal representation of a message returned by the service."""

    id: str
    from_: str
    to: str
    date: str
    subject: str


class MessageDetail(MessageSummary):
    """Full representation of a message including the body."""

    body: str


class OperationResponse(BaseModel):
    """Standard envelope for write operations."""

    success: bool
    message: str
