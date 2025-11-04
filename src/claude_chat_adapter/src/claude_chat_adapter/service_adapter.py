from __future__ import annotations

from claude_chat_service_client.api.chat import send_chat_message_chat_post
from claude_chat_service_client.models.chat_request import ChatRequest

from claude_chat_api import AbstractClaudeChatAPI, Message, MessageRole
from claude_chat_service_client import client as generated_client


class ServiceClaudeChat(AbstractClaudeChatAPI):
    """Concrete implementation which delegates to the HTTP service.

    Authentication is provided via the `session_token` cookie which the
    service sets after a successful OAuth flow. Provide that cookie value
    when constructing this adapter or later via `set_session_token`.
    """

    def __init__(self, *, base_url: str, session_token: str | None = None) -> None:
        self._base_url = base_url
        self._client = generated_client.Client(base_url=base_url, raise_on_unexpected_status=True)
        if session_token:
            self.set_session_token(session_token)

    def set_session_token(self, session_token: str) -> None:
        """Attach/replace the `session_token` cookie for authenticated calls."""
        # The generated client returns a new instance, but also mutates the internal httpx client if created.
        self._client = self._client.with_cookies({"session_token": session_token})

    def send_message(self, prompt: str, user_id: str) -> Message:
        """Send a prompt to the service and return the assistant's reply.

        Note: `user_id` is part of the abstract contract but not sent over the
        wire; the service resolves the user from the `session_token` cookie.
        """
        # Prepare request payload for the generated SDK
        body = ChatRequest(prompt=prompt)

        # Use detailed call to inspect status codes explicitly
        response = send_chat_message_chat_post.sync_detailed(client=self._client, body=body)

        if response.status_code == 200 and response.parsed is not None:
            # Map the generated model back to the contract model
            service_message = response.parsed
            # Ensure role is assistant per contract; keep content from service
            return Message(role=MessageRole.ASSISTANT, content=str(service_message.content))

        if response.status_code == 400:
            # Common case: user hasn't stored a Claude API key yet
            detail = response.content.decode("utf-8", errors="ignore") if hasattr(response.content, "decode") else str(response.content)
            raise RuntimeError(f"Chat request rejected (400): {detail}")

        if response.status_code == 401:
            raise PermissionError("Not authenticated. Ensure session_token cookie is set.")

        if response.status_code == 422:
            raise ValueError("Validation failed for chat request (422).")

        # Unexpected status is already handled by raise_on_unexpected_status, but keep a guard
        raise RuntimeError(f"Unexpected status: {response.status_code}")

