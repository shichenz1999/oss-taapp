"""Abstract contract for the Claude chat service."""

from abc import ABC, abstractmethod

from .models import Message


class AbstractClaudeChatAPI(ABC):
    """Expose the minimal contract required by the service."""

    @abstractmethod
    def send_message(self, prompt: str, user_id: str) -> Message:
        """Send a single user prompt to the AI and return the response.

        Implementations should remain stateless: each call must succeed without
        referencing prior prompts or conversation history.
        """
        raise NotImplementedError


__all__ = ["AbstractClaudeChatAPI"]
