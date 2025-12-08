# claude_chat_impl/src/claude_chat_impl/__init__.py

"""Public exports for the Claude chat implementation package."""

from .claude_impl import ClaudeClient, get_ai_interface_impl
from .claude_impl import register as _register_client
from .settings import settings

__all__ = [
    "ClaudeClient",
    "get_ai_interface_impl",
    "register",
    "settings",
]


def register() -> None:
    """Register the Claude client implementation."""
    _register_client()


register()
