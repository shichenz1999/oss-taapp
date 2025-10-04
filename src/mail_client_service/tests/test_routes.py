"""Skeleton tests for mail_client_service routes."""

from collections.abc import Generator
from typing import Any
from unittest.mock import Mock, create_autospec

import pytest
from fastapi.testclient import TestClient

from mail_client_api import Client
from mail_client_service import app

client = TestClient(app)

def test_list_messages_skeleton() -> None:
    pytest.skip("Implement GET /messages test")


def test_get_message_success(
    api_client: TestClient,
) -> None:
    # Message Object
    fake_mail_client = Mock(spec=mail_client_api.Client)
    msg = {
        "id":"msg-1",
        "from_":"msg-1@from.com",
        "to":"msg-1@to.com",
        "date":"10/03/2025",
        "subject":"msg-1 subject",
        "body":"msg-1 body",
    }

    # mock return value
    fake_mail_client.get_message.return_value = msg

    # send request
    response = api_client.get("/messages/msg-1")

    # assert
    assert response.status_code == 200
    assert response.json() == {
        "id":"msg-1",
        "from_":"msg-1@from.com",
        "to":"msg-1@to.com",
        "date":"10/03/2025",
        "subject":"msg-1 subject",
        "body":"msg-1 body",
    }



def test_get_message_not_found(
    api_client: TestClient,
) -> None:
    
    # arrange
    fake_mail_client = Mock(spec=mail_client_api.Client)
    fake_mail_client.get_message.side_effect = ValueError("not found")

    response = api_client.get("/messages/nonexistent")

    # assert
    assert response.status_code == 500
    print(response.json())
    assert response.json() == {'message': 'Requested entity was not found.', 'domain': 'global', 'reason': 'notFound'}
    

def test_mark_as_read_success() -> None:
    # ARRANGE
    mock_client = Mock(spec=Client)
    mock_client.mark_as_read.return_value = True
    message_id = "msg_123"

    # ACT
    response = client.post(f"/messages/{message_id}/mark-as-read")

    # ASSERT
    assert response.status_code == 200
    assert response.json() == {"status": "read"}
    mock_client.mark_as_read.assert_called_once_with(message_id)

def test_mark_as_read_failure() -> None:
    # ARRANGE
    mock_client = Mock(spec=Client)
    mock_client.mark_as_read.return_value = False
    message_id = "msg_123"

    # ACT
    response = client.post(f"/messages/{message_id}/mark-as-read")

    # ASSERT
    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to mark message as read"}
    mock_client.mark_as_read.assert_called_once_with(message_id)


def test_delete_message_success() -> None:
    # ARRANGE
    mock_client = Mock(spec=Client)
    mock_client.delete_message.return_value = True

    # ACT
    response = client.delete("/messages/msg-123")

    # ASSERT
    assert response.status_code == 200
    assert response.json() == {"status": "deleted"}
    mock_client.delete_message.assert_called_once_with("msg-123")


def test_delete_message_failure() -> None:
    # ARRANGE
    mock_client = Mock(spec=Client)
    mock_client.delete_message.return_value = False

    # ACT
    response = client.delete("/messages/msg-123")

    # ASSERT
    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to delete message"}
    mock_client.delete_message.assert_called_once_with("msg-123")
