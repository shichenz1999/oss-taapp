"""Claude-backed session implementation."""

from __future__ import annotations

import uuid
from typing import Iterable

from anthropic import Anthropic
from anthropic.types import Message as ClaudeAPIMessage

from ai_conversation_api.message import Message
from ai_conversation_api.session import Session
from ai_conversation_impl.message_impl import (
    ClaudeMessage,
    create_assistant_message,
    create_user_message,
)
from ai_conversation_impl.storage import TinySessionStore


DEFAULT_MODEL = "claude-3-haiku-20240307"
DEFAULT_MAX_TOKENS = 1024


class ClaudeSession(Session):
    """Maintain state for a single Claude conversation."""

    def __init__(
        self,
        *,
        anthropic_client: Anthropic,
        session_id: str,
        store: TinySessionStore,
        model: str | None = None,
        max_output_tokens: int | None = None,
    ) -> None:
        self._client = anthropic_client
        self._id = session_id
        self._store = store
        self._model = model or DEFAULT_MODEL
        self._max_tokens = max_output_tokens or DEFAULT_MAX_TOKENS

    @property
    def id(self) -> str:
        return self._id

    @property
    def model(self) -> str:
        return self._model

    @property
    def history(self) -> Iterable[Message]:
        records = self._store.list_messages(self._id)
        return tuple(
            ClaudeMessage(record["message_id"], record["role"], record["content"])
            for record in records
        )

    def send(self, content: str) -> Message:
        user_message = create_user_message(_new_id(), content)
        self._store.append_message(self._id, user_message.id, user_message.role, user_message.content)
        records = self._store.list_messages(self._id)

        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=_history_payload(records),
        )

        assistant_message = create_assistant_message(
            response.id or _new_id(),
            _collect_text(response),
        )
        self._store.append_message(
            self._id,
            assistant_message.id,
            assistant_message.role,
            assistant_message.content,
        )
        return assistant_message

    def reset(self) -> None:
        self._store.clear_session_messages(self._id)


def _collect_text(message: ClaudeAPIMessage) -> str:
    content = getattr(message, "content", None) or []
    parts: list[str] = []
    for item in content:
        text = getattr(item, "text", None)
        if text:
            parts.append(text)
    return "".join(parts)


def _history_payload(records: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{"role": record["role"], "content": record["content"]} for record in records]


def _new_id() -> str:
    return str(uuid.uuid4())
