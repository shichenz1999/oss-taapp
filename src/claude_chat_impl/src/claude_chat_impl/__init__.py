# claude_chat_impl/src/claude_chat_impl/__init__.py

"""This package contains the concrete implementation of the
Claude Chat API.

It exports the main implementation class, the auth manager,
and the settings for use by other components.
"""

from .auth_manager import AuthManager
from .implementation import ClaudeChatImplementation, MissingClaudeAPIKeyError
from .settings import settings
from .user_key_store import ClaudeAPIKeyRepository

__all__ = [
    "AuthManager",
    "ClaudeAPIKeyRepository",
    "ClaudeChatImplementation",
    "MissingClaudeAPIKeyError",
    "settings",
]
