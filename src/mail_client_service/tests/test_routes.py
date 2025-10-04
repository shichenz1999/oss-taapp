"""Skeleton tests for mail_client_service routes."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from mail_client_api import Client
from mail_client_service import app

client = TestClient(app)

def test_list_messages_skeleton() -> None:
    pytest.skip("Implement GET /messages test")


def test_get_message_skeleton() -> None:
    pytest.skip("Implement GET /messages/{message_id} test")


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
