from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException

import gmail_client_impl
import mail_client_api
from mail_client_api import Message

app = FastAPI()
__all__ = ["app"]


@lru_cache(maxsize=1)
def _client_factory() -> mail_client_api.Client:
    return mail_client_api.get_client(interactive=True)


def get_mail_client() -> mail_client_api.Client:
    return _client_factory()


def _serialize_message(msg: Message) -> dict[str, str]:
    raise NotImplementedError("Implement message serialization")


@app.get("/messages")
def list_messages(
    max_results: int = 10,
    client: mail_client_api.Client = Depends(get_mail_client),
) -> list[dict[str, str]]:
    raise NotImplementedError("Implement GET /messages")

def message_to_dict(msg: Message) -> dict:
    """Serialize Message object to dict for JSON response"""
    return {
        "id": msg.id,
        "from": msg.from_,
        "to": msg.to,
        "date": msg.date,
        "subject": msg.subject,
        "body": msg.body,
    }

@app.get("/messages/{message_id}")
def get_message(
    message_id: str,
    client: mail_client_api.Client = Depends(get_mail_client),
) -> dict:
    """get a message by message id"""
    try:
        msg = client.get_message(message_id)
        return message_to_dict(msg) 
    except HTTPException as e:
        raise HTTPException(status_code=500, detail=str(e))
    # raise NotImplementedError("Implement GET /messages/{message_id}")


@app.post("/messages/{message_id}/mark-as-read")
def mark_as_read(
    message_id: str,
    client: mail_client_api.Client = Depends(get_mail_client),
) -> dict[str, str]:
    if not client.mark_as_read(message_id):
        raise HTTPException(status_code=500, detail="Failed to mark message as read")

    return {"status": "read"}


@app.delete("/messages/{message_id}")
def delete_message(
    message_id: str,
    client: mail_client_api.Client = Depends(get_mail_client),
) -> dict[str, str]:
    if not client.delete_message(message_id):
        raise HTTPException(status_code=500, detail="Failed to delete message")

    return {"status": "deleted"}
