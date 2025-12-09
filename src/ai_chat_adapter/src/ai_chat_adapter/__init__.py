"""Package exports for ai_chat_adapter."""

from __future__ import annotations

from ai_chat_api import AIInterface
import ai_chat_api
from ai_chat_service_client.client import Client as ServiceClient

from .adapter import AiChatAdapter

__all__ = ["AiChatAdapter", "register"]


def register(*, base_url: str) -> None:
    """Register AiChatAdapter as the default ai_chat_api interface."""

    def _factory() -> AIInterface:
        client = ServiceClient(base_url=base_url)
        return AiChatAdapter(client=client)

    ai_chat_api.get_ai_interface = _factory
