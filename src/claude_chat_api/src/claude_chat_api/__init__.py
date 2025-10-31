# src/claude_chat_api/__init__.py

"""
This package defines the abstract API contract for the
Claude Chat Service.

It exports the core data models and the abstract interface.
"""

from .models import Message, MessageRole
from .api import AbstractClaudeChatAPI

# This makes imports cleaner for other packages
# e.g., 'from claude_chat_api import Message, AbstractClaudeChatAPI'
__all__ = [
    "Message",
    "MessageRole",
    "AbstractClaudeChatAPI"
]