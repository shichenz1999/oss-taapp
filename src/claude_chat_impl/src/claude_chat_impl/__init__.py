# claude_chat_impl/src/claude_chat_impl/__init__.py

"""Expose the concrete implementation of the Claude Chat API.

Exports the main implementation class, the auth manager, and shared settings for
other components.
"""

from .auth_manager import AuthManager
from .implementation import ClaudeChatImplementation
from .settings import settings

__all__ = [
    "AuthManager",
    "ClaudeChatImplementation",
    "settings"
]
