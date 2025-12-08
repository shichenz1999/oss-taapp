"""Package exports for ai_chat_adapter."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

import ai_chat_api
from ai_chat_service_api_client.fast_api_client.client import AuthenticatedClient
from ai_chat_service_api_client.fast_api_client.client import Client as ServiceClient

from .adapter import AiChatServiceAdapter

ClientProtocol: TypeAlias = AuthenticatedClient | ServiceClient
ClientFactory = Callable[[], ClientProtocol]

__all__ = ["AiChatServiceAdapter", "register"]


def register(*, base_url: str | None = None, client_factory: ClientFactory | None = None) -> None:
    """Register AiChatServiceAdapter as the default ai_chat_api client."""
    factory = client_factory
    if factory is None:
        if base_url is None:
            missing_base_url_msg = "base_url is required when client_factory is not provided."
            raise ValueError(missing_base_url_msg)

        def default_factory() -> ClientProtocol:
            return ServiceClient(base_url=base_url)

        factory = default_factory

    def _factory() -> ai_chat_api.AIInterface:
        return AiChatServiceAdapter(client=factory())

    ai_chat_api.get_ai_interface = _factory
