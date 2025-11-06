# claude_chat_impl/src/claude_chat_impl/claude_impl.py
"""Anthropic-backed implementation of the ai_chat_api.Client contract."""

import anthropic
import ai_chat_api

from ai_chat_api import Client, Message

from .settings import settings
from .message_impl import anthropic_response_to_message

claude_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


class ClaudeClient(Client):
    """Concrete chat client that proxies calls to Anthropic's Claude API."""

    def send_message(self, prompt: str, user_id: str) -> Message:
        """Send a single prompt and return the assistant's response."""

        _ = user_id

        api_response = claude_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        return anthropic_response_to_message(api_response)


def get_client_impl() -> ClaudeClient:
    """Return a new ClaudeClient instance."""
    return ClaudeClient()


def register() -> None:
    """Register the Claude client factory with the ai_chat_api contract."""
    ai_chat_api.get_client = get_client_impl
