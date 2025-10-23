from unittest.mock import MagicMock, patch

import mail_client_api
import pytest

from mail_client_adapter import ServiceMailClient, ServiceMessage
from mail_client_service_client.fast_api_client.models.message_detail import MessageDetail
from mail_client_service_client.fast_api_client.models.message_summary import MessageSummary
from mail_client_service_client.fast_api_client.models.operation_response import OperationResponse


@pytest.fixture(autouse=True)
def reset_mail_client_api(monkeypatch):
    # ensure get_client is not permanently modified by other tests
    if hasattr(mail_client_api, "get_client"):
        monkeypatch.setattr(mail_client_api, "get_client", mail_client_api.get_client, raising=False)


def test_service_message_adapts_generated_payload():
    # ARRANGE
    payload = MessageDetail.from_dict(
        {
            "id": "123",
            "from_": "a@a.com",
            "to": "b@b.com",
            "date": "2025-01-01",
            "subject": "hello",
            "body": "world",
        }
    )

    # ACT
    msg = ServiceMessage(payload)

    # ASSERT
    assert msg.id == "123"
    assert msg.from_ == "a@a.com"
    assert msg.to == "b@b.com"
    assert msg.date == "2025-01-01"
    assert msg.subject == "hello"
    assert msg.body == "world"


@patch("mail_client_service_client.fast_api_client.client.Client")
@patch("mail_client_service_client.fast_api_client.api.default.get_message_messages_message_id_get.sync")
@patch("mail_client_service_client.fast_api_client.api.default.list_messages_messages_get.sync")
@patch("mail_client_service_client.fast_api_client.api.default.delete_message_messages_message_id_delete.sync")
@patch("mail_client_service_client.fast_api_client.api.default.mark_as_read_messages_message_id_mark_as_read_post.sync")
def test_service_mail_client_methods(mock_mark, mock_delete, mock_list, mock_get, mock_client_ctor):
    # ARRANGE generated client ctor
    mock_client_ctor.return_value = MagicMock()

    # ARRANGE API responses
    mock_list.return_value = [
        MessageSummary.from_dict(
            {
                "id": "1",
                "from_": "sender1@example.com",
                "to": "recipient@example.com",
                "date": "2025-10-03",
                "subject": "s1",
            }
        ),
        MessageSummary.from_dict(
            {
                "id": "2",
                "from_": "sender2@example.com",
                "to": "recipient@example.com",
                "date": "2025-10-04",
                "subject": "s2",
            }
        ),
    ]
    # get_message will be called 3 times total: once explicitly, twice during get_messages iteration
    mock_get.side_effect = [
        MessageDetail.from_dict(
            {
                "id": "1",
                "from_": "sender1@example.com",
                "to": "recipient@example.com",
                "date": "2025-10-03",
                "subject": "s1",
                "body": "body-1",
            }
        ),
        MessageDetail.from_dict(
            {
                "id": "1",
                "from_": "sender1@example.com",
                "to": "recipient@example.com",
                "date": "2025-10-03",
                "subject": "s1-full",
                "body": "body-1-full",
            }
        ),
        MessageDetail.from_dict(
            {
                "id": "2",
                "from_": "sender2@example.com",
                "to": "recipient@example.com",
                "date": "2025-10-04",
                "subject": "s2-full",
                "body": "body-2-full",
            }
        ),
    ]
    mock_delete.return_value = OperationResponse(success=True, message="deleted")
    mock_mark.return_value = OperationResponse(success=True, message="marked as read")

    client = ServiceMailClient(base_url="http://x")

    # get_message
    m1 = client.get_message("1")
    assert isinstance(m1, mail_client_api.Message)
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
