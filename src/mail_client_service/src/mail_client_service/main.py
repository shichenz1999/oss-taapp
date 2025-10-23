"""Mail client service routes and dependencies."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

import gmail_client_impl  # noqa: F401
import mail_client_api
from mail_client_service.models import MessageDetail, MessageSummary, OperationResponse

app = FastAPI()


@lru_cache(maxsize=1)
def _client_factory() -> mail_client_api.Client:
    """Return a cached mail client implementation."""
    return mail_client_api.get_client(interactive=False)


def get_mail_client() -> mail_client_api.Client:
    """Dependency hook for retrieving the cached mail client."""
    return _client_factory()


def reset_client_cache() -> None:
    """Clear the cached mail client instance."""
    _client_factory.cache_clear()


def msg_to_summary(msg: mail_client_api.Message) -> MessageSummary:
    """Convert a contract-level message into a summary model."""
    return MessageSummary(
        id=msg.id,
        from_=msg.from_,
        to=msg.to,
        date=msg.date,
        subject=msg.subject,
    )


def msg_to_detail(msg: mail_client_api.Message) -> MessageDetail:
    """Convert a contract-level message into a detail model."""
    return MessageDetail(
        id=msg.id,
        from_=msg.from_,
        to=msg.to,
        date=msg.date,
        subject=msg.subject,
        body=msg.body,
    )


@app.get("/messages", response_model=list[MessageSummary])  # noqa: FAST001
def list_messages(
    client: Annotated[mail_client_api.Client, Depends(get_mail_client)],
    max_results: int = 10,
) -> list[MessageSummary]:
    """List message summaries sourced from the underlying client."""
    try:
        msgs = client.get_messages(max_results=max_results)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [msg_to_summary(msg) for msg in msgs]


@app.get("/messages/{message_id}", response_model=MessageDetail)  # noqa: FAST001
def get_message(
    message_id: str,
    client: Annotated[mail_client_api.Client, Depends(get_mail_client)],
) -> MessageDetail:
    """Return the detailed message for a given identifier."""
    try:
        msg = client.get_message(message_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return msg_to_detail(msg)


@app.post("/messages/{message_id}/mark-as-read", response_model=OperationResponse)  # noqa: FAST001
def mark_as_read(
    message_id: str,
    client: Annotated[mail_client_api.Client, Depends(get_mail_client)],
) -> OperationResponse:
    """Mark the targeted message as read."""
    if not client.mark_as_read(message_id):
        raise HTTPException(status_code=500, detail="Failed to mark message as read")

    return OperationResponse(success=True, message="marked as read")


@app.delete("/messages/{message_id}", response_model=OperationResponse)  # noqa: FAST001
def delete_message(
    message_id: str,
    client: Annotated[mail_client_api.Client, Depends(get_mail_client)],
) -> OperationResponse:
    """Delete the targeted message."""
    if not client.delete_message(message_id):
        raise HTTPException(status_code=500, detail="Failed to delete message")

    return OperationResponse(success=True, message="deleted")
