from __future__ import annotations

from ai_conversation_api.client import Client
import ai_conversation_api
import ai_conversation_impl  # noqa: F401  # ensure register() runs on import


def get_conversation_client() -> Client:
    return ai_conversation_api.get_client()
