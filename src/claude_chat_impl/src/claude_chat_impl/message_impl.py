# claude_chat_impl/src/claude_chat_impl/message_impl.py

"""Translate Anthropic responses into ai_chat_api.Message objects."""

import ai_chat_api

from typing import Any

from ai_chat_api import Message


class ClaudeMessage(Message):
    """Concrete chat message returned by the Claude implementation."""

    def __init__(self, role: str, content: str) -> None:
        self._role = role
        self._content = content

    @property
    def role(self) -> str:
        return self._role

    @property
    def content(self) -> str:
        return self._content


def anthropic_response_to_message(response: Any) -> Message:
    """Convert an Anthropic SDK response to the ai_chat_api.Message contract."""
    role = response.role
    text = response.content[0].text

    return ClaudeMessage(role=role, content=text)


def get_message_impl(role: str, content: str) -> Message:
    """Return a ClaudeMessage built from plain role/content data."""
    return ClaudeMessage(role=role, content=content)


def register() -> None:
    """Register the Claude message factory with the ai_chat_api contract."""
    ai_chat_api.get_message = get_message_impl
