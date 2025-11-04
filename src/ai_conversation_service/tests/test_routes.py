from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import pytest
from fastapi.testclient import TestClient

from ai_conversation_service import app
from ai_conversation_service.dependencies import get_conversation_client


@dataclass
class FakeMessage:
    id: str
    role: str
    content: str


@dataclass
class FakeSession:
    session_id: str
    history_records: list[FakeMessage] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.session_id

    @property
    def model(self) -> str | None:
        return "claude-3-haiku"

    @property
    def history(self) -> Iterable[FakeMessage]:
        return tuple(self.history_records)

    def send(self, content: str) -> FakeMessage:
        user = FakeMessage(id=f"{self.session_id}-u-{len(self.history_records)}", role="user", content=content)
        assistant = FakeMessage(
            id=f"{self.session_id}-a-{len(self.history_records) + 1}",
            role="assistant",
            content=f"Echo: {content}",
        )
        self.history_records.extend([user, assistant])
        return assistant

    def reset(self) -> None:
        self.history_records.clear()


class FakeClient:
    def __init__(self) -> None:
        self.sessions: dict[str, FakeSession] = {}

    def create_session(self) -> FakeSession:
        session_id = f"s{len(self.sessions) + 1}"
        session = FakeSession(session_id=session_id)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> FakeSession:
        if session_id not in self.sessions:
            raise ValueError("Session not found")
        return self.sessions[session_id]

    def list_sessions(self) -> Iterable[FakeSession]:
        return tuple(self.sessions.values())

    def delete_session(self, session_id: str) -> bool:
        return self.sessions.pop(session_id, None) is not None


@pytest.fixture(autouse=True)
def override_dependency():
    client = FakeClient()
    app.dependency_overrides[get_conversation_client] = lambda: client
    try:
        yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def api() -> TestClient:
    return TestClient(app)


def test_create_and_list(api: TestClient) -> None:
    api.post("/sessions")
    response = api.get("/sessions")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_missing_returns_404(api: TestClient) -> None:
    assert api.get("/sessions/missing").status_code == 404


def test_send_message_returns_reply(api: TestClient, override_dependency: FakeClient) -> None:
    session = override_dependency.create_session()
    response = api.post(f"/sessions/{session.id}/messages", json={"content": "hi"})
    assert response.status_code == 201
    assert response.json()["message"]["content"] == "Echo: hi"


def test_reset_session_clears_history(api: TestClient, override_dependency: FakeClient) -> None:
    session = override_dependency.create_session()
    session.send("ping")
    assert api.post(f"/sessions/{session.id}/reset").status_code == 204
    detail = api.get(f"/sessions/{session.id}").json()
    assert detail["history"] == []


def test_delete_session(api: TestClient, override_dependency: FakeClient) -> None:
    session = override_dependency.create_session()
    response = api.delete(f"/sessions/{session.id}")
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "deleted"}
    assert api.delete(f"/sessions/{session.id}").status_code == 404
