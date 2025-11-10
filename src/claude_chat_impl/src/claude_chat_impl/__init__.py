# claude_chat_impl/src/claude_chat_impl/__init__.py

"""Public exports for the Claude chat implementation package."""

from .claude_impl import ClaudeClient, get_client_impl
from .claude_impl import register as _register_client
from .message_impl import ClaudeMessage, get_message_impl
from .message_impl import register as _register_message
from .settings import settings

__all__ = [
    "ClaudeClient",
    "ClaudeMessage",
    "get_client_impl",
    "get_message_impl",
    "register",
    "settings",
]


def register() -> None:
    """Register the Claude client and message implementations."""
    _register_client()
    _register_message()


register()
