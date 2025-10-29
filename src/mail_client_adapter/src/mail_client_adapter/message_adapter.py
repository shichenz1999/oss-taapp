"""Adapter that exposes generated message detail models via the API contract."""

from mail_client_api import Message
from mail_client_service_client.fast_api_client.models.message_detail import MessageDetail


class ServiceMessage(Message):
    """Expose a generated `MessageDetail` instance through the `mail_client_api` contract."""

    def __init__(self, detail: MessageDetail) -> None:
        """Store the detail payload returned by the service."""
        self._detail = detail

    @property
    def id(self) -> str:
        """Return the message identifier."""
        return self._detail.id

    @property
    def from_(self) -> str:
        """Return the sender address."""
        return self._detail.from_

    @property
    def to(self) -> str:
        """Return the recipient list."""
        return self._detail.to

    @property
    def date(self) -> str:
        """Return the message date."""
        return self._detail.date

    @property
    def subject(self) -> str:
        """Return the message subject."""
        return self._detail.subject

    @property
    def body(self) -> str:
        """Return the message body."""
        return self._detail.body
