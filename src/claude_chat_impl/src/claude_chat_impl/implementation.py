# claude_chat_impl/src/claude_chat_impl/implementation.py

import anthropic

# 1. Import the "Contract" and "Models" from our API package
from claude_chat_api import AbstractClaudeChatAPI, Message, MessageRole

# 2. Import our settings
from .settings import settings
from .user_key_store import ClaudeAPIKeyRepository


class MissingClaudeAPIKeyError(RuntimeError):
    """Raised when a user tries to chat without registering their Claude API key."""


class ClaudeChatImplementation(AbstractClaudeChatAPI):
    """The concrete implementation of the AbstractClaudeChatAPI.
    This class provides the real logic to call the Anthropic (Claude) API.
    """

    def __init__(self, key_repository: ClaudeAPIKeyRepository | None = None) -> None:
        self._key_repository = key_repository or ClaudeAPIKeyRepository(
            settings.CLAUDE_KEY_DB_PATH
        )

    def _create_client(self, api_key: str) -> anthropic.Anthropic:
        """Factory so we can swap the client easily during testing."""
        return anthropic.Anthropic(api_key=api_key)

    def send_message(self, prompt: str, user_id: str) -> Message:
        """Sends a single user prompt to the AI and returns the response.
        
        This implementation is STATELESS, matching our minimal API.
        It does not store or use chat history.
        """
        # We can use the user_id for logging or auditing
        print(f"[ClaudeImpl] Processing request for user_id: {user_id}")

        api_key = self._key_repository.get_api_key(user_id)
        if api_key is None:
            raise MissingClaudeAPIKeyError(
                "No Claude API key registered for this user. "
                "Please set your key before chatting."
            )

        claude_client = self._create_client(api_key=api_key)

        try:
            # 1. Call the Claude API
            api_response = claude_client.messages.create(
                model="claude-3-haiku-20240307", # Fast and cheap model
                max_tokens=1024,
                system="You are a helpful assistant.",
                messages=[
                    # Since we are stateless, we only send the new prompt
                    {"role": "user", "content": prompt}
                ]
            )

            # 2. Extract the text from the response
            if api_response.content and len(api_response.content) > 0:
                ai_text = api_response.content[0].text
            else:
                ai_text = "I'm sorry, I couldn't generate a response."

            # 3. Package the response into our API's 'Message' model
            return Message(
                role=MessageRole.ASSISTANT,
                content=ai_text
            )

        except anthropic.APIError as e:
            print(f"Error calling Anthropic API: {e}")
            # We re-raise the error for the service layer to handle
            raise
