"""Concrete message helpers for Claude sessions."""

from __future__ import annotations

from ai_conversation_api.message import Message


class ClaudeMessage(Message):
    """Concrete message representation."""

    def __init__(self, message_id: str, role: str, content: str) -> None:
        self._id = message_id
        self._role = role
        self._content = content

    def __str__(self) -> str:
        return self._content

    @property
    def id(self) -> str:
        return self._id

    @property
    def role(self) -> str:
        return self._role

    @property
    def content(self) -> str:
        return self._content


def create_user_message(message_id: str, content: str) -> ClaudeMessage:
    """Factory for user messages."""
    return ClaudeMessage(message_id, "user", content)


def create_assistant_message(message_id: str, content: str) -> ClaudeMessage:
    """Factory for assistant messages."""
    return ClaudeMessage(message_id, "assistant", content)
