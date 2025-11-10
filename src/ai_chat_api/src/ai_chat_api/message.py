# src/ai_chat_api/message.py

"""Message contract - Core message representation."""

from abc import ABC, abstractmethod

__all__ = ["Message", "get_message"]


class Message(ABC):
    """Abstract base class representing a chat message."""

    @property
    @abstractmethod
    def role(self) -> str:
        """Return the role associated with this message."""
        raise NotImplementedError

    @property
    @abstractmethod
    def content(self) -> str:
        """Return the textual content of the message."""
        raise NotImplementedError


def get_message(role: str, content: str) -> Message:
    """Return an implementation-specific Message instance."""
    raise NotImplementedError
