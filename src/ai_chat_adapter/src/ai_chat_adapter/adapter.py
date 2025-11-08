"""Adapter that translates the ai_chat_api contract into calls to the service API client."""

from __future__ import annotations

from http import HTTPStatus
from typing import Union

from ai_chat_api.client import Client as AbstractClient
from ai_chat_api.message import Message as AbstractMessage

import ai_chat_api
from ai_chat_service_api_client.fast_api_client.api.chat import send_chat_message_chat_post
from ai_chat_service_api_client.fast_api_client.client import AuthenticatedClient
from ai_chat_service_api_client.fast_api_client.client import Client as ServiceClient
from ai_chat_service_api_client.fast_api_client.models.chat_request import ChatRequest as ServiceChatRequest
from ai_chat_service_api_client.fast_api_client.models.chat_response import ChatResponse as ServiceChatResponse
from ai_chat_service_api_client.fast_api_client.models.http_validation_error import HTTPValidationError
from ai_chat_service_api_client.fast_api_client.types import Response

__all__ = ["AiChatServiceAdapter"]

ClientProtocol = Union[AuthenticatedClient, ServiceClient]


class AiChatServiceAdapter(AbstractClient):
    """Concrete ai_chat_api.Client that proxies requests to the FastAPI service."""

    def __init__(self, client: ClientProtocol) -> None:
        self._client = client

    def send_message(self, prompt: str, user_id: str) -> AbstractMessage:
        """Send a message through the remote service and return the reply."""
        _ = user_id  # Service derives the user from Auth headers/cookies on the client instance.

        request_body = ServiceChatRequest(prompt=prompt)
        response = send_chat_message_chat_post.sync_detailed(client=self._client, body=request_body)

        return self._build_message_from_response(response)

    def _build_message_from_response(
        self, response: Response[ServiceChatResponse | HTTPValidationError]
    ) -> AbstractMessage:
        if response.status_code != HTTPStatus.OK:
            raise RuntimeError(
                f"Chat service returned unexpected status {response.status_code}: {response.content!r}"
            )

        parsed = response.parsed

        if parsed is None:
            raise RuntimeError("Chat service returned an empty body.")

        if isinstance(parsed, HTTPValidationError):
            raise RuntimeError(f"Chat service validation error: {parsed.to_dict()}")

        if not isinstance(parsed, ServiceChatResponse):
            raise RuntimeError(f"Unexpected chat response type: {type(parsed)}")

        return ai_chat_api.get_message(role=parsed.role, content=parsed.content)
