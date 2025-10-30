"""Claude client implementation using the session abstraction."""

from __future__ import annotations

import os
from collections.abc import Iterable

from anthropic import Anthropic

from ai_conversation_api.client import Client
from ai_conversation_api.session import Session
from ai_conversation_impl.session_impl import ClaudeSession
from ai_conversation_impl.storage import TinySessionStore

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class ClaudeClient(Client):
    """Concrete client managing Claude-backed sessions."""

    def __init__(self, *, api_key: str | None = None, store: TinySessionStore | None = None) -> None:
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("Missing Anthropic API key. Set ANTHROPIC_API_KEY or pass api_key.")

        self._client = Anthropic(api_key=key)
        self._store = store or TinySessionStore()

    def create_session(self) -> Session:
        """Create a new session with an auto-generated identifier."""
        session_id = self._store.create_session()
        return ClaudeSession(
            anthropic_client=self._client,
            session_id=session_id,
            store=self._store,
        )

    def get_session(self, session_id: str) -> Session:
        if not self._store.session_exists(session_id):
            raise ValueError(f"Session '{session_id}' does not exist.")
        return ClaudeSession(
            anthropic_client=self._client,
            session_id=session_id,
            store=self._store,
        )

    def list_sessions(self) -> Iterable[Session]:
        sessions: list[Session] = []
        for session_id in self._store.list_sessions():
            sessions.append(
                ClaudeSession(
                    anthropic_client=self._client,
                    session_id=session_id,
                    store=self._store,
                )
            )
        return tuple(sessions)

    def delete_session(self, session_id: str) -> bool:
        return self._store.delete_session(session_id)
