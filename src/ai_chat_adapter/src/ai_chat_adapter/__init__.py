"""Package exports for ai_chat_adapter."""

from __future__ import annotations

from collections.abc import Callable

import ai_chat_api

from ai_chat_service_api_client.fast_api_client.client import AuthenticatedClient, Client as ServiceClient

from .adapter import AiChatServiceAdapter

ClientProtocol = AuthenticatedClient | ServiceClient
ClientFactory = Callable[[], ClientProtocol]

__all__ = ["AiChatServiceAdapter", "register"]


def register(*, base_url: str | None = None, client_factory: ClientFactory | None = None) -> None:
    """Register AiChatServiceAdapter as the default ai_chat_api client."""

    if client_factory is None:
        if base_url is None:
            raise ValueError("base_url is required when client_factory is not provided.")

        def client_factory() -> ClientProtocol:  # type: ignore[no-redef]
            return ServiceClient(base_url=base_url)

    def _factory() -> ai_chat_api.Client:
        return AiChatServiceAdapter(client=client_factory())

    ai_chat_api.get_client = _factory
