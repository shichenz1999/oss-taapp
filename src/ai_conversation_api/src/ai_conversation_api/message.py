"""Core AI conversation message contracts and factory placeholders."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

__all__ = ["Message", "Conversation", "get_message", "get_conversation"]


class Message(ABC):
    """Abstract base class representing a single exchange in a conversation."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Return the unique identifier of the message."""
        raise NotImplementedError

    @property
    @abstractmethod
    def role(self) -> str:
        """Return the speaker role (for example: 'user', 'assistant', 'system')."""
        raise NotImplementedError

    @property
    @abstractmethod
    def content(self) -> str:
        """Return the text content of the message."""
        raise NotImplementedError


class Conversation(ABC):
    """Abstract base class representing a conversation thread."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Return the unique identifier of the conversation."""
        raise NotImplementedError

    @property
    @abstractmethod
    def messages(self) -> Iterable[Message]:
        """Return the messages that belong to the conversation."""
        raise NotImplementedError


def get_message(message_id: str, payload: dict[str, object]) -> Message:
    """Return a Message instance constructed from provider payload."""
    raise NotImplementedError


def get_conversation(conversation_id: str, payload: dict[str, object]) -> Conversation:
    """Return a Conversation instance constructed from provider payload."""
    raise NotImplementedError
