"""Package exports for ai_chat_adapter."""

from __future__ import annotations

import ai_chat_api
from ai_chat_api import AIInterface

from .adapter import AiChatAdapter, build_service_client

__all__ = ["AiChatAdapter", "register"]


def register(*, base_url: str) -> None:
    """Register AiChatAdapter as the default ai_chat_api interface."""

    def _factory() -> AIInterface:
        client = build_service_client(base_url=base_url)
        return AiChatAdapter(client=client)

    ai_chat_api.get_ai_interface = _factory
