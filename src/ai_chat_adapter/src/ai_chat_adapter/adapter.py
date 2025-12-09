"""Adapter that translates the ai_chat_api contract into calls to the service API client."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from ai_chat_api import AIInterface
from ai_chat_service_client.api.chat import send_chat_message_chat_post
from ai_chat_service_client.client import Client as ServiceClient
from ai_chat_service_client.models.chat_request import ChatRequest
from ai_chat_service_client.models.chat_response import ChatResponse
from ai_chat_service_client.models.http_validation_error import HTTPValidationError
from ai_chat_service_client.types import Response, UNSET

__all__ = ["AiChatAdapter"]

class AiChatAdapter(AIInterface):
    """Concrete ai_chat_api implementation that proxies requests to the FastAPI service."""

    def __init__(self, client: ServiceClient) -> None:
        """Store the generated FastAPI client instance."""
        self._client = client

    def generate_response(
        self,
        user_input: str,
        system_prompt: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        """Send a message through the remote service and return the raw response payload."""
        request_body = ChatRequest(
            user_input=user_input,
            system_prompt=system_prompt if system_prompt is not None else UNSET,
            response_schema=response_schema if response_schema is not None else UNSET,
        )

        response = send_chat_message_chat_post.sync_detailed(client=self._client, body=request_body)
        return self._extract_response(response)

    def _extract_response(
        self,
        response: "Response[ChatResponse | HTTPValidationError]",
    ) -> str | dict[str, Any]:
        if response.status_code != HTTPStatus.OK:
            error = f"Chat service returned unexpected status {response.status_code}: {response.content!r}"
            raise RuntimeError(error)

        parsed = response.parsed
        if parsed is None:
            raise RuntimeError("Chat service returned an empty body.")
        if isinstance(parsed, HTTPValidationError):
            raise TypeError(f"Chat service validation error: {parsed.to_dict()}")
        if not isinstance(parsed, ChatResponse):
            raise TypeError(f"Unexpected chat response type: {type(parsed)}")
        result = parsed.response
        if hasattr(result, "to_dict"):
            return result.to_dict()
        return result
