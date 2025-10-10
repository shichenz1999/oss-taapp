from unittest.mock import patch, MagicMock

import mail_client_api
import pytest

from mail_client_adapter import ServiceMailClient, ServiceMessage


class _DummyModel:
    def __init__(self, **kwargs: object) -> None:
        self.additional_properties = kwargs


@pytest.fixture(autouse=True)
def reset_mail_client_api(monkeypatch):
    # ensure get_client is not permanently modified by other tests
    if hasattr(mail_client_api, "get_client"):
        monkeypatch.setattr(mail_client_api, "get_client", mail_client_api.get_client, raising=False)


def test_service_message_adapts_generated_payload():
    payload = _DummyModel(id="123", from_="a@a.com", to="b@b.com", date="d", subject="s", body="b")
    msg = ServiceMessage(payload)
    assert msg.id == "123"
    assert msg.from_ == "a@a.com"
    assert msg.to == "b@b.com"
    assert msg.date == "d"
    assert msg.subject == "s"
    assert msg.body == "b"


@patch("mail_client_service_client.fast_api_client.client.Client")
@patch("mail_client_service_client.fast_api_client.api.default.get_message_messages_message_id_get.sync")
@patch("mail_client_service_client.fast_api_client.api.default.list_messages_messages_get.sync")
@patch("mail_client_service_client.fast_api_client.api.default.delete_message_messages_message_id_delete.sync")
@patch("mail_client_service_client.fast_api_client.api.default.mark_as_read_messages_message_id_mark_as_read_post.sync")
def test_service_mail_client_methods(mock_mark, mock_delete, mock_list, mock_get, mock_client_ctor):
    # Arrange generated client ctor
    mock_client_ctor.return_value = MagicMock()

    # Arrange API responses
    mock_list.return_value = [
        _DummyModel(id="1"),
        _DummyModel(id="2"),
    ]
    # get_message will be called 3 times total: once explicitly, twice during get_messages iteration
    mock_get.side_effect = [
        _DummyModel(id="1", subject="s1"),  # explicit get_message("1")
        _DummyModel(id="1", subject="s1_full"),  # for iterator resolving id "1"
        _DummyModel(id="2", subject="s2_full"),  # for iterator resolving id "2"
    ]
    mock_delete.return_value = _DummyModel(status="deleted")
    mock_mark.return_value = _DummyModel(status="read")

    client = ServiceMailClient(base_url="http://x")

    # get_message
    m1 = client.get_message("1")
    assert isinstance(m1, ServiceMessage)
    assert m1.id == "1"

    # get_messages should iterate and resolve full messages via get
    messages = list(client.get_messages(max_results=2))
    assert [m.id for m in messages] == ["1", "2"]

    # delete
    assert client.delete_message("1") is True

    # mark as read
    assert client.mark_as_read("1") is True

    # Ensure correct calls into generated client
    mock_list.assert_called_once()
    assert mock_get.call_count == 3  # 1 from explicit get_message, 2 from iterator
    mock_delete.assert_called_once()
    mock_mark.assert_called_once()
