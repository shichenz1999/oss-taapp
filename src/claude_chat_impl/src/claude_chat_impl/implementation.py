"""Concrete implementation of the Claude chat API contract."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Iterable

import anthropic

from claude_chat_api import AbstractClaudeChatAPI, Message, MessageRole

from .settings import settings

LOGGER = logging.getLogger(__name__)


def _extract_text(blocks: Iterable[Any]) -> str:
    """Return the first text block produced by Claude."""
    for block in blocks:
        text: str | None = None
        if isinstance(block, dict):
            raw = block.get("text")
            if isinstance(raw, str):
                text = raw
        else:
            raw_attr = getattr(block, "text", None)
            if isinstance(raw_attr, str):
                text = raw_attr
        if text:
            return text
    return "I'm sorry, I couldn't generate a response."


try:
    claude_client = anthropic.Anthropic(api_key=settings.CLAUDE_API_KEY)
except Exception:
    LOGGER.exception("Failed to initialize Anthropic client")
    raise


class ClaudeChatImplementation(AbstractClaudeChatAPI):
    """Bridge the abstract contract to the Anthropic Claude API."""

    def send_message(self, prompt: str, user_id: str) -> Message:
        """Send a single prompt to Claude and return the assistant response."""
        LOGGER.info("Processing request for user_id: %s", user_id)

        try:
            api_response = claude_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                system="You are a helpful assistant.",
                messages=[{"role": "user", "content": prompt}],
            )
            content = cast("Iterable[Any]", getattr(api_response, "content", []))
            ai_text = _extract_text(content)
            return Message(role=MessageRole.ASSISTANT, content=ai_text)
        except anthropic.APIError:
            LOGGER.exception("Error calling Anthropic API")
            raise
