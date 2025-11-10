"""Adapter that translates the ai_chat_api contract into calls to the service API client."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, TypeAlias

from ai_chat_api.client import Client as AbstractClient

import ai_chat_api
from ai_chat_service_api_client.fast_api_client.api.chat import send_chat_message_chat_post
from ai_chat_service_api_client.fast_api_client.client import AuthenticatedClient
from ai_chat_service_api_client.fast_api_client.client import Client as ServiceClient
from ai_chat_service_api_client.fast_api_client.models.chat_request import ChatRequest as ServiceChatRequest
from ai_chat_service_api_client.fast_api_client.models.chat_response import (
    ChatResponse as ServiceChatResponse,
)
from ai_chat_service_api_client.fast_api_client.models.http_validation_error import HTTPValidationError

if TYPE_CHECKING:
    from ai_chat_api.message import Message as AbstractMessage

    from ai_chat_service_api_client.fast_api_client.types import Response

__all__ = ["AiChatServiceAdapter"]

ClientProtocol: TypeAlias = AuthenticatedClient | ServiceClient


class AiChatServiceAdapter(AbstractClient):
    """Concrete ai_chat_api.Client that proxies requests to the FastAPI service."""

    def __init__(self, client: ClientProtocol) -> None:
        """Store the generated FastAPI client instance."""
        self._client = client

    def send_message(self, prompt: str, user_id: str) -> AbstractMessage:
        """Send a message through the remote service and return the reply."""
        _ = user_id  # Service derives the user from Auth headers/cookies on the client instance.

        request_body = ServiceChatRequest(prompt=prompt)
        response = send_chat_message_chat_post.sync_detailed(client=self._client, body=request_body)

        return self._build_message_from_response(response)

    def _build_message_from_response(self, response: Response[ServiceChatResponse | HTTPValidationError]) -> AbstractMessage:
        if response.status_code != HTTPStatus.OK:
            status_message = f"Chat service returned unexpected status {response.status_code}: {response.content!r}"
            raise RuntimeError(status_message)

        parsed = response.parsed

        if parsed is None:
            empty_body_message = "Chat service returned an empty body."
            raise RuntimeError(empty_body_message)

        if isinstance(parsed, HTTPValidationError):
            validation_message = f"Chat service validation error: {parsed.to_dict()}"
            raise TypeError(validation_message)

        if not isinstance(parsed, ServiceChatResponse):
            type_message = f"Unexpected chat response type: {type(parsed)}"
            raise TypeError(type_message)

        return ai_chat_api.get_message(role=parsed.role, content=parsed.content)
