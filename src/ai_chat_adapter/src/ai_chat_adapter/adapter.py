"""Adapter that translates the ai_chat_api contract into calls to the service API client."""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, TypeAlias

from ai_chat_api import AIInterface, AIStructuredResponse
from ai_chat_service_api_client.fast_api_client.client import AuthenticatedClient
from ai_chat_service_api_client.fast_api_client.client import Client as ServiceClient

if TYPE_CHECKING:
    import httpx

__all__ = ["AiChatServiceAdapter"]

ClientProtocol: TypeAlias = AuthenticatedClient | ServiceClient


class AiChatServiceAdapter(AIInterface):
    """Concrete ai_chat_api AIInterface that proxies requests to the FastAPI service."""

    def __init__(self, client: ClientProtocol) -> None:
        """Store the generated FastAPI client instance."""
        self._client = client

    def generate_response(
        self,
        user_input: str,
        system_prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> AIStructuredResponse:
        """Send a message through the remote service and return the structured reply."""
        payload: dict[str, Any] = {"user_input": user_input, "system_prompt": system_prompt}
        if response_schema is not None:
            payload["response_schema"] = response_schema

        http_response = self._client.get_httpx_client().request(
            "post",
            "/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        return self._build_structured_response(http_response)

    def _build_structured_response(self, http_response: "httpx.Response") -> AIStructuredResponse:
        if http_response.status_code != HTTPStatus.OK:
            status_message = f"Chat service returned unexpected status {http_response.status_code}: {http_response.content!r}"
            raise RuntimeError(status_message)

        try:
            payload = http_response.json()
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive path
            error_message = f"Chat service returned invalid JSON: {http_response.content!r}"
            raise RuntimeError(error_message) from exc

        try:
            return AIStructuredResponse.model_validate(payload)
        except Exception as exc:
            validation_message = f"Chat service response did not match AIStructuredResponse: {payload!r}"
            raise TypeError(validation_message) from exc
