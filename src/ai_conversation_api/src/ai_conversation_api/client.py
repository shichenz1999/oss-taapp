"""Client abstractions for managing AI chat sessions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any

from .session import Session
from .message import Message


class Client(ABC):
    """Creates and manages chat sessions."""

    @abstractmethod
    def create_session(self, *, name: str | None = None, **kwargs: Any) -> Session:
        """Create a brand-new chat session and return it."""
        raise NotImplementedError

    @abstractmethod
    def get_session(self, session_id: str) -> Session:
        """Retrieve an existing chat session by ID."""
        raise NotImplementedError

    @abstractmethod
    def list_sessions(self) -> Iterable[Session]:
        """Iterate over known chat sessions."""
        raise NotImplementedError

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Remove a chat session; return True if it existed."""
        raise NotImplementedError

    # Optional convenience method mirroring Session.send
    def send(
        self,
        content: str,
        *,
        session_id: str | None = None,
    ) -> Message:
        """Send a message via an existing or newly created session."""
        session = self.get_session(session_id) if session_id else self.create_session()
        return session.send(content)


def get_client(*, api_key: str | None = None, **kwargs: Any) -> Client:
    """Return an instance of a conversation client."""
    raise NotImplementedError
