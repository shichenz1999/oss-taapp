from __future__ import annotations

from pydantic import BaseModel


class MessageEnvelope(BaseModel):
    id: str
    role: str
    content: str


class SessionSummary(BaseModel):
    id: str
    model: str | None = None


class SessionDetail(SessionSummary):
    history: list[MessageEnvelope]


class SendMessageRequest(BaseModel):
    content: str


class SendMessageResponse(BaseModel):
    message: MessageEnvelope


class OperationResponse(BaseModel):
    success: bool
    message: str
