"""Message contracts for AI conversations."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Message(ABC):
    """Represents a single utterance within a conversation."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Return the unique identifier of this message."""
        raise NotImplementedError

    @property
    @abstractmethod
    def role(self) -> str:
        """Return the role (e.g., 'user', 'assistant', 'system')."""
        raise NotImplementedError

    @property
    @abstractmethod
    def content(self) -> str:
        """Return the textual content associated with this message."""
        raise NotImplementedError

    def __str__(self) -> str:
        """Return the message content when printed."""
        return self.content
