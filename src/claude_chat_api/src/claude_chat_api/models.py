# src/claude_chat_api/models.py

from enum import Enum

from pydantic import BaseModel


class MessageRole(str, Enum):
    """Defines the role of the entity creating a message.
    'user' is for the end-user, 'assistant' is for the AI.
    """

    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """A single chat message. This is the fundamental data model
    for our API.
    """

    role: MessageRole
    content: str
