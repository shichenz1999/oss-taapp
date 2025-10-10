"""Adapters for message payloads returned by the service SDK."""

from collections.abc import Mapping
from typing import Any, cast

from mail_client_api import Message


def _to_mapping(payload: object) -> Mapping[str, Any]:
    """Normalize SDK payload-like objects into a Mapping[str, Any]."""
    if isinstance(payload, Mapping):
        return payload
    if hasattr(payload, "additional_properties"):
        return cast("Mapping[str, Any]", payload.additional_properties)
    if hasattr(payload, "to_dict"):
        return cast("Mapping[str, Any]", payload.to_dict())
    # Keep the error simple to satisfy Ruff's exception message style rules.
    typename = type(payload).__name__
    msg = f"Unsupported payload type: {typename}"
    raise TypeError(msg)


def _to_str(value: object) -> str:
    """Convert possibly non-string values into strings; None becomes empty string."""
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


class ServiceMessage(Message):
    """Concrete Message backed by a mapping-like payload from the service SDK."""

    def __init__(self, payload: object) -> None:
        """Create a message by adapting a raw SDK payload to our interface."""
        data = _to_mapping(payload)
        self._id = _to_str(data.get("id"))
        self._from = _to_str(data.get("from_"))
        self._to = _to_str(data.get("to"))
        self._date = _to_str(data.get("date"))
        self._subject = _to_str(data.get("subject"))
        self._body = _to_str(data.get("body"))

    @property
    def id(self) -> str:
        """Unique message identifier."""
        return self._id

    @property
    def from_(self) -> str:
        """Sender email address."""
        return self._from

    @property
    def to(self) -> str:
        """Recipient email address."""
        return self._to

    @property
    def date(self) -> str:
        """Message date string."""
        return self._date

    @property
    def subject(self) -> str:
        """Message subject."""
        return self._subject

    @property
    def body(self) -> str:
        """Message body text."""
        return self._body
