# src/ai_chat_api/client.py

"""Core AI chat interface definitions."""

from abc import ABC, abstractmethod

from .message import Message

__all__ = ["Client", "get_client"]


class Client(ABC):
    """Abstract base class representing an AI chat backend."""

    @abstractmethod
    def send_message(self, prompt: str, user_id: str) -> Message:
        """Send a single prompt for the specified user and return the assistant reply."""
        raise NotImplementedError


def get_client() -> Client:
    """Return an instance of an AI chat client."""
    raise NotImplementedError
