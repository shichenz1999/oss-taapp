"""Skeleton tests for mail_client_service routes."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from mail_client_api import Client, get_mail_client
from mail_client_service import app

client = TestClient(app)

@pytest.fixture
def mock_client():
    """Fixture to mock the mail client dependency."""
    mock_client = Mock(spec=Client)
    app.dependency_overrides[get_mail_client] = lambda: mock_client
    yield mock_client
    app.dependency_overrides = {}

def test_list_messages_skeleton(mock_client) -> None:
    pytest.skip("Implement GET /messages test")


def test_get_message_success(mock_client) -> None:
    # Message Object
    msg = {
        "id":"msg-1",
        "from_":"msg-1@from.com",
        "to":"msg-1@to.com",
        "date":"10/03/2025",
        "subject":"msg-1 subject",
        "body":"msg-1 body",
    }

    # mock return value
    mock_client.get_message.return_value = msg

    # send request
    response = client.get("/messages/msg-1")

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



def test_get_message_not_found(mock_client) -> None:
    
    # arrange
    mock_client.get_message.side_effect = ValueError("not found")

    response = client.get("/messages/nonexistent")

    # assert
    assert response.status_code == 500
    print(response.json())
    assert response.json() == {'message': 'Requested entity was not found.', 'domain': 'global', 'reason': 'notFound'}
    

def test_mark_as_read_success(mock_client) -> None:
    # ARRANGE
    mock_client.mark_as_read.return_value = True
    message_id = "msg_123"

    # ACT
    response = client.post(f"/messages/{message_id}/mark-as-read")

    # ASSERT
    assert response.status_code == 200
    assert response.json() == {"status": "read"}
    mock_client.mark_as_read.assert_called_once_with(message_id)

def test_mark_as_read_failure(mock_client) -> None:
    # ARRANGE
    mock_client.mark_as_read.return_value = False
    message_id = "msg_123"

    # ACT
    response = client.post(f"/messages/{message_id}/mark-as-read")

    # ASSERT
    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to mark message as read"}
    mock_client.mark_as_read.assert_called_once_with(message_id)


def test_delete_message_success(mock_client) -> None:
    # ARRANGE
    mock_client.delete_message.return_value = True

    # ACT
    response = client.delete("/messages/msg-123")

    # ASSERT
    assert response.status_code == 200
    assert response.json() == {"status": "deleted"}
    mock_client.delete_message.assert_called_once_with("msg-123")


def test_delete_message_failure(mock_client) -> None:
    # ARRANGE
    mock_client.delete_message.return_value = False

    # ACT
    response = client.delete("/messages/msg-123")

    # ASSERT
    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to delete message"}
    mock_client.delete_message.assert_called_once_with("msg-123")
