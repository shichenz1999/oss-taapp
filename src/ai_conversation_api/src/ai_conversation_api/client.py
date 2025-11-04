"""Core AI conversation client contract definitions."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from ai_conversation_api.message import Conversation, Message

__all__ = ["Client", "get_client"]


class Client(ABC):
    """Abstract base class for an AI conversation client."""

    @abstractmethod
    def create_conversation(self) -> Conversation:
        """Create a new conversation thread."""
        raise NotImplementedError

    @abstractmethod
    def send_message(
        self,
        content: str,
        *,
        conversation_id: str | None = None,
        stream: bool = False,
    ) -> Message | Iterator[Message]:
        """Send a message; when `conversation_id` is None, implementations should
        create or reuse a default conversation internally and return the reply.
        """
        raise NotImplementedError

    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Conversation:
        """Return a conversation along with its accumulated messages."""
        raise NotImplementedError

    @abstractmethod
    def list_messages(
        self,
        conversation_id: str,
        *,
        max_results: int | None = None,
    ) -> Iterator[Message]:
        """Yield messages that belong to the given conversation."""
        raise NotImplementedError

    @abstractmethod
    def list_conversations(self, max_results: int = 10) -> Iterator[Conversation]:
        """Yield available conversations (paged as needed)."""
        raise NotImplementedError

    @abstractmethod
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation when supported."""
        raise NotImplementedError


def get_client(*, api_key: str | None = None, **kwargs: Any) -> Client:
    """Return an AI conversation client implementation."""
    raise NotImplementedError
