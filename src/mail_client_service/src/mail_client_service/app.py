"""FastAPI service exposing the mail client API over HTTP."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException

import gmail_client_impl  # noqa: F401
import mail_client_api
from mail_client_api import Message

app = FastAPI()

@lru_cache(maxsize=1)
def _client_factory() -> mail_client_api.Client:
    return mail_client_api.get_client(interactive=False)


def get_mail_client() -> mail_client_api.Client:
    return _client_factory()


def msg_summary_to_dict(msg: Message) -> dict[str, str]:
    return {
        "id": msg.id,
        "from_": msg.from_,
        "to": msg.to,
        "date": msg.date,
        "subject": msg.subject,
    }


def msg_to_dict(msg: Message) -> dict[str, str]:
    return {
        "id": msg.id,
        "from_": msg.from_,
        "to": msg.to,
        "date": msg.date,
        "subject": msg.subject,
        "body": msg.body,
    }


@app.get("/messages")
def list_messages(
    client: Annotated[mail_client_api.Client, Depends(get_mail_client)],
    max_results: int = 10,
) -> list[dict[str, str]]:
    try:
        msgs = client.get_messages(max_results=max_results)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [msg_summary_to_dict(msg) for msg in msgs]


@app.get("/messages/{message_id}")
def get_message(
    message_id: str,
    client: Annotated[mail_client_api.Client, Depends(get_mail_client)],
) -> dict[str, str]:
    """Get a message by message id."""
    try:
        msg = client.get_message(message_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return msg_to_dict(msg)


@app.post("/messages/{message_id}/mark-as-read")
def mark_as_read(
    message_id: str,
    client: Annotated[mail_client_api.Client, Depends(get_mail_client)],
) -> dict[str, str]:
    if not client.mark_as_read(message_id):
        raise HTTPException(status_code=500, detail="Failed to mark message as read")

    return {"status": "read"}


@app.delete("/messages/{message_id}")
def delete_message(
    message_id: str,
    client: Annotated[mail_client_api.Client, Depends(get_mail_client)],
) -> dict[str, str]:
    if not client.delete_message(message_id):
        raise HTTPException(status_code=500, detail="Failed to delete message")

    return {"status": "deleted"}
