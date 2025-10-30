# src/claude_chat_api/api.py

from abc import ABC, abstractmethod
from .models import Message

class AbstractClaudeChatAPI(ABC):
    """
    The abstract interface (API Contract) for the Claude Chat Service.

    This defines the minimum viable functionality required to test
    the entire HW2 architecture, including the OAuth flow.
    """

    @abstractmethod
    def send_message(self, prompt: str, user_id: str) -> Message:
        """
        Sends a single user prompt to the AI and returns the response.

        This is designed to be a stateless, single-shot function.
        It does not store or manage conversation history.

        Args:
            prompt: The text input from the user.
            user_id: The authenticated ID of the user (from the OAuth flow).
                     This is required to test the protected endpoint.

        Returns:
            A Message object with the 'assistant' role, containing
            the AI's reply.
        
        Raises:
            (Not specified here, but implementations might raise
             AuthError, ServiceError, etc.)
        """
        # The '@abstractmethod' decorator handles the enforcement.
        # The '...' (Ellipsis) is a valid, empty placeholder.
        ...