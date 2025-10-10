import pytest

from mail_client_adapter import ServiceMessage


class DummyWithAdditional:
    def __init__(self, **kwargs: object) -> None:
        self.additional_properties = kwargs


def test_service_message_accepts_mapping_payload():
    payload = {"id": "1", "from_": "a", "to": "b", "date": "d", "subject": "s", "body": "c"}
    msg = ServiceMessage(payload)
    assert (msg.id, msg.from_, msg.to, msg.date, msg.subject, msg.body) == ("1", "a", "b", "d", "s", "c")


def test_service_message_accepts_additional_properties_payload():
    payload = DummyWithAdditional(id="2", from_="fa", to="tb", date="dd", subject="ss", body="bb")
    msg = ServiceMessage(payload)
    assert msg.id == "2"


def test_service_message_accepts_to_dict_payload():
    class D:
        def to_dict(self):
            return {"id": "3", "from_": None, "to": 7, "date": "", "subject": 9.5, "body": True}

    msg = ServiceMessage(D())
    # None and non-str get stringified appropriately
    assert (msg.id, msg.from_, msg.to, msg.date, msg.subject, msg.body) == ("3", "", "7", "", "9.5", "True")


def test_service_message_unsupported_payload_raises_type_error():
    class NotSupported:  # no additional_properties, no to_dict, not a Mapping
        pass

    with pytest.raises(TypeError):
        ServiceMessage(NotSupported())
