"""Convenience exports for Claude conversation implementation."""

from __future__ import annotations

import ai_conversation_api
from ai_conversation_api import Client

from .claude_client_impl import ClaudeClient
from .session_impl import ClaudeSession

__all__ = ["ClaudeClient", "ClaudeSession", "register"]


def _get_client_impl(*, api_key: str | None = None, **kwargs) -> Client:
    """Return a Claude-backed client instance."""
    return ClaudeClient(api_key=api_key, **kwargs)


def register() -> None:
    """Hook our factory into ai_conversation_api."""
    ai_conversation_api.get_client = _get_client_impl


# mirror Gmail: register on import
register()
