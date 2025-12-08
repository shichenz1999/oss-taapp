"""Abstract interfaces for AI APIs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

__all__ = ["AIInterface", "AIStructuredResponse", "get_ai_interface"]


class AIStructuredResponse(BaseModel):
    """Structured AI response capturing an action intent and its parameters."""

    intent: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class AIInterface(ABC):
    """The contract for AI services."""

    @abstractmethod
    def generate_response(
        self,
        user_input: str,
        system_prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> str | AIStructuredResponse:
        """Generate a response from the AI.

        :param user_input: The text provided by the chat user.
        :param system_prompt: The instruction set (e.g., "You are a helpful assistant...").
        :param response_schema: An optional JSON schema (dict).
                                If provided, the AI must return a structured Dict matching this schema.
                                If None, the AI returns a conversational String.

        :return: A string (conversation) or an ``AIStructuredResponse`` instance.
        """
        raise NotImplementedError


def get_ai_interface() -> AIInterface:
    """Return the configured AI interface implementation."""
    raise NotImplementedError
