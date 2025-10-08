from typing import Any, Mapping
from mail_client_api import Message

def _to_mapping(payload: Any) -> Mapping[str, Any]:
    if isinstance(payload, Mapping):
        return payload
    if hasattr(payload, "additional_properties"):
        return payload.additional_properties
    if hasattr(payload, "to_dict"):
        return payload.to_dict()
    raise TypeError(f"Unsupported payload type: {type(payload)!r}")

def _to_str(value: Any) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)

class ServiceMessage(Message):
    def __init__(self, payload: Any) -> None:
        data = _to_mapping(payload)
        self._id = _to_str(data.get("id"))
        self._from = _to_str(data.get("from_"))
        self._to = _to_str(data.get("to"))
        self._date = _to_str(data.get("date"))
        self._subject = _to_str(data.get("subject"))
        self._body = _to_str(data.get("body"))

    @property
    def id(self) -> str:
        return self._id

    @property
    def from_(self) -> str:
        return self._from

    @property
    def to(self) -> str:
        return self._to

    @property
    def date(self) -> str:
        return self._date

    @property
    def subject(self) -> str:
        return self._subject

    @property
    def body(self) -> str:
        return self._body
