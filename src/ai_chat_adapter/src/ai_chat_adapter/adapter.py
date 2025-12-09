"""Adapter that translates the ai_chat_api contract into calls to the service API client."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any, cast

from ai_chat_service_client.api.chat import send_chat_message_chat_post
from ai_chat_service_client.client import Client as ServiceClient
from ai_chat_service_client.models.chat_request import ChatRequest
from ai_chat_service_client.models.chat_response import ChatResponse
from ai_chat_service_client.models.http_validation_error import HTTPValidationError
from ai_chat_service_client.types import UNSET, Response

from ai_chat_api import AIInterface

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = ["AiChatAdapter", "build_service_client"]


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
        response: Response[ChatResponse | HTTPValidationError],
    ) -> str | dict[str, Any]:
        if response.status_code != HTTPStatus.OK:
            error = f"Chat service returned unexpected status {response.status_code}: {response.content!r}"
            raise RuntimeError(error)

        parsed = response.parsed
        if parsed is None:
            empty_body_message = "Chat service returned an empty body."
            raise RuntimeError(empty_body_message)
        if isinstance(parsed, HTTPValidationError):
            validation_error_message = f"Chat service validation error: {parsed.to_dict()}"
            raise TypeError(validation_error_message)
        if not isinstance(parsed, ChatResponse):
            unexpected_type_message = f"Unexpected chat response type: {type(parsed)}"
            raise TypeError(unexpected_type_message)
        result = parsed.response
        if hasattr(result, "to_dict"):
            to_dict: Callable[[], dict[str, Any]] = result.to_dict
            return to_dict()
        return cast("str", result)



def build_service_client(*, base_url: str) -> ServiceClient:
    """Create a service client for the configured API endpoint."""
    return ServiceClient(base_url=base_url)
