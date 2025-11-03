"""Data models shared by Claude chat components."""

from enum import Enum

from pydantic import BaseModel


class MessageRole(str, Enum):
    """Identify whether a message came from the user or assistant."""

    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """Representation of a single Claude chat message."""

    role: MessageRole
    content: str
