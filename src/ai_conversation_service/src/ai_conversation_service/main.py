from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status

from ai_conversation_api.client import Client
from ai_conversation_service.dependencies import get_conversation_client
from ai_conversation_service.models import (
    MessageEnvelope,
    OperationResponse,
    SendMessageRequest,
    SendMessageResponse,
    SessionDetail,
    SessionSummary,
)

app = FastAPI()


def _message_to_envelope(message) -> MessageEnvelope:
    return MessageEnvelope(id=message.id, role=message.role, content=message.content)


def _session_to_summary(session) -> SessionSummary:
    return SessionSummary(id=session.id, model=session.model)


def _session_to_detail(session) -> SessionDetail:
    history = [_message_to_envelope(msg) for msg in session.history]
    return SessionDetail(id=session.id, model=session.model, history=history)


@app.get("/sessions", response_model=list[SessionSummary])
def list_sessions(client: Client = Depends(get_conversation_client)) -> list[SessionSummary]:
    try:
        return [_session_to_summary(session) for session in client.list_sessions()]
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@app.post("/sessions", response_model=SessionSummary, status_code=status.HTTP_201_CREATED)
def create_session(client: Client = Depends(get_conversation_client)) -> SessionSummary:
    try:
        return _session_to_summary(client.create_session())
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@app.get("/sessions/{session_id}", response_model=SessionDetail)
def get_session(session_id: str, client: Client = Depends(get_conversation_client)) -> SessionDetail:
    try:
        session = client.get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return _session_to_detail(session)


@app.delete("/sessions/{session_id}", response_model=OperationResponse)
def delete_session(session_id: str, client: Client = Depends(get_conversation_client)) -> OperationResponse:
    try:
        removed = client.delete_session(session_id)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return OperationResponse(success=True, message="deleted")


@app.post(
    "/sessions/{session_id}/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_message(
    session_id: str,
    payload: SendMessageRequest,
    client: Client = Depends(get_conversation_client),
) -> SendMessageResponse:
    try:
        session = client.get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    reply = session.send(payload.content)
    return SendMessageResponse(message=_message_to_envelope(reply))


@app.post("/sessions/{session_id}/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_session(session_id: str, client: Client = Depends(get_conversation_client)) -> None:
    try:
        session = client.get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    session.reset()
