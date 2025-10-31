# claude_chat_impl/src/claude_chat_impl/implementation.py

import anthropic

# 1. Import the "Contract" and "Models" from our API package
from claude_chat_api import AbstractClaudeChatAPI, Message, MessageRole

# 2. Import our settings
from .settings import settings

# 3. Create a single, module-level Anthropic client
# This is best practice for performance and connection management.
try:
    claude_client = anthropic.Anthropic(
        api_key=settings.CLAUDE_API_KEY
    )
except Exception as e:
    print(f"Failed to initialize Anthropic client: {e}")
    raise


class ClaudeChatImplementation(AbstractClaudeChatAPI):
    """
    The concrete implementation of the AbstractClaudeChatAPI.
    This class provides the real logic to call the Anthropic (Claude) API.
    """

    def send_message(self, prompt: str, user_id: str) -> Message:
        """
        Sends a single user prompt to the AI and returns the response.
        
        This implementation is STATELESS, matching our minimal API.
        It does not store or use chat history.
        """
        
        # We can use the user_id for logging or auditing
        print(f"[ClaudeImpl] Processing request for user_id: {user_id}")

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