# claude_chat_impl/src/claude_chat_impl/__init__.py

"""Public exports for the Claude chat implementation package."""

from .claude_impl import ClaudeAIInterface, get_ai_interface_impl
from .claude_impl import register as _register_ai_interface
from .settings import settings

__all__ = ["ClaudeAIInterface", "get_ai_interface_impl", "register", "settings"]


def register() -> None:
    """Register the Claude AI interface implementation."""
    _register_ai_interface()


register()
