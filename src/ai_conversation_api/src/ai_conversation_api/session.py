"""Session abstractions for AI conversations."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from .message import Message


class Session(ABC):
    """Encapsulates a single conversational context with an LLM."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Stable identifier for this session."""
        raise NotImplementedError

    @property
    @abstractmethod
    def model(self) -> str | None:
        """Underlying model used by this session (when known)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def history(self) -> Iterable[Message]:
        """Return an immutable view of the accumulated dialogue."""
        raise NotImplementedError

    @abstractmethod
    def send(self, content: str) -> Message:
        """Append a user message and return the assistant reply."""
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        """Clear stored history/context for this session."""
        raise NotImplementedError
