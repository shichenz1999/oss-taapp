"""Abstract interfaces for AI APIs."""

from abc import ABC, abstractmethod
from typing import Any


class AIInterface(ABC):
    """The contract for AI services."""

    @abstractmethod
    def generate_response(
        self,
        user_input: str,
        system_prompt: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        """Generate a response from the AI.

        :param user_input: The text provided by the chat user.
        :param system_prompt: Optional instruction set (e.g., "You are a helpful assistant...").
        :param response_schema: An optional JSON schema (dict).
                                If provided, the AI must return a structured Dict matching this schema.
                                If None, the AI returns a conversational String.

        :return: A string (conversation) or a Dict (structured action data).
        """
        raise NotImplementedError


def get_ai_interface() -> AIInterface:
    """Return the default AI interface implementation."""
    raise NotImplementedError
