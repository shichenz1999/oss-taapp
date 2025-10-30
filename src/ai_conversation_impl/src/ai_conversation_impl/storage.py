"""TinyDB-backed persistence for Claude conversations."""

from __future__ import annotations

import uuid
from typing import Iterable

try:
    from tinydb import TinyDB, Query  # type: ignore[import-untyped]
except ImportError as exc:  # pragma: no cover
    msg = "tinydb is required for TinySessionStore. Install it via `pip install tinydb`."
    raise RuntimeError(msg) from exc


class TinySessionStore:
    """Persist conversations using TinyDB (JSON) storage."""

    def __init__(self, db_path: str = "claude_sessions.json") -> None:
        self._db = TinyDB(db_path)
        self._sessions = self._db.table("sessions")
        self._messages = self._db.table("messages")

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions.insert({"id": session_id})
        return session_id

    def append_message(self, session_id: str, message_id: str, role: str, content: str) -> None:
        self._messages.insert(
            {
                "session_id": session_id,
                "message_id": message_id,
                "role": role,
                "content": content,
            }
        )

    def list_messages(self, session_id: str) -> list[dict[str, str]]:
        Message = Query()
        docs = self._messages.search(Message.session_id == session_id)
        docs.sort(key=lambda d: d.doc_id)
        return [
            {
                "message_id": doc["message_id"],
                "role": doc["role"],
                "content": doc["content"],
            }
            for doc in docs
        ]

    def delete_session(self, session_id: str) -> bool:
        Session = Query()
        removed = self._sessions.remove(Session.id == session_id)
        Message = Query()
        self._messages.remove(Message.session_id == session_id)
        return bool(removed)

    def clear_session_messages(self, session_id: str) -> None:
        Message = Query()
        self._messages.remove(Message.session_id == session_id)

    def session_exists(self, session_id: str) -> bool:
        Session = Query()
        return self._sessions.contains(Session.id == session_id)

    def list_sessions(self) -> Iterable[str]:
        return tuple(doc["id"] for doc in self._sessions.all())
