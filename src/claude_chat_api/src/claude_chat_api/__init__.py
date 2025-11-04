# src/claude_chat_api/__init__.py

"""This package defines the abstract API contract for the
Claude Chat Service.

It exports the core data models and the abstract interface.
"""

from .api import AbstractClaudeChatAPI
from .models import Message, MessageRole

# This makes imports cleaner for other packages
# e.g., 'from claude_chat_api import Message, AbstractClaudeChatAPI'
__all__ = ["AbstractClaudeChatAPI", "Message", "MessageRole"]
