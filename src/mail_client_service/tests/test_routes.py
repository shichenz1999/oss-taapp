"""Unit tests for mail_client_service routes."""

from collections.abc import Iterator
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from mail_client_api import Client
from mail_client_service import app, get_mail_client, reset_client_cache

client = TestClient(app)


@pytest.fixture
def mock_client() -> Iterator[Mock]:
    """Fixture to mock the mail client dependency."""
    mock_client = Mock(spec=Client)
    app.dependency_overrides[get_mail_client] = lambda: mock_client
    yield mock_client
    app.dependency_overrides.pop(get_mail_client, None)


def test_get_mail_client_uses_cached_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    """The service should cache the real client factory."""
    reset_client_cache()

    calls: list[bool] = []
    sentinel = object()

    def fake_get_client(*, interactive: bool = False) -> object:
        calls.append(interactive)
        return sentinel

    monkeypatch.setattr("mail_client_api.get_client", fake_get_client)

    first = get_mail_client()
    second = get_mail_client()

    assert first is sentinel
    assert second is sentinel
    assert calls == [False]

    reset_client_cache()


def test_list_messages_success(mock_client: Mock) -> None:
    # ARRANGE
    messages = [
        SimpleNamespace(
            id="msg-1",
            from_="sender1@example.com",
            to="recipient@example.com",
            date="2025-10-03",
            subject="msg-1 subject",
            body="msg-1 body",
        ),
        SimpleNamespace(
            id="msg-2",
            from_="sender2@example.com",
            to="recipient@example.com",
            date="2025-10-04",
            subject="msg-2 subject",
            body="msg-2 body",
        ),
    ]
    mock_client.get_messages.return_value = messages

    # ACT
    response = client.get("/messages", params={"max_results": 2})

    # ASSERT
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "msg-1",
            "from_": "sender1@example.com",
            "to": "recipient@example.com",
            "date": "2025-10-03",
            "subject": "msg-1 subject",
        },
        {
            "id": "msg-2",
            "from_": "sender2@example.com",
            "to": "recipient@example.com",
            "date": "2025-10-04",
            "subject": "msg-2 subject",
        },
    ]
    mock_client.get_messages.assert_called_once_with(max_results=2)


def test_list_messages_failure(mock_client: Mock) -> None:
    # ARRANGE
    mock_client.get_messages.side_effect = RuntimeError("boom")

    # ACT
    response = client.get("/messages")

    # ASSERT
    assert response.status_code == 500
    assert response.json() == {"detail": "boom"}
    mock_client.get_messages.assert_called_once_with(max_results=10)


def test_get_message_success(mock_client: Mock) -> None:
    # Message Object
    msg = SimpleNamespace(
        id="msg-1",
        from_="msg-1@from.com",
        to="msg-1@to.com",
        date="10/03/2025",
        subject="msg-1 subject",
        body="msg-1 body",
    )

    # mock return value
    mock_client.get_message.return_value = msg

    # send request
    response = client.get("/messages/msg-1")

    # assert
    assert response.status_code == 200
    assert response.json() == {
        "id": "msg-1",
        "from_": "msg-1@from.com",
        "to": "msg-1@to.com",
        "date": "10/03/2025",
        "subject": "msg-1 subject",
        "body": "msg-1 body",
    }
    mock_client.get_message.assert_called_once_with("msg-1")


def test_get_message_not_found(mock_client: Mock) -> None:
    # arrange
    mock_client.get_message.side_effect = ValueError("not found")

    # act
    response = client.get("/messages/nonexistent")

    # assert
    assert response.status_code == 500
    assert response.json() == {"detail": "not found"}
    mock_client.get_message.assert_called_once_with("nonexistent")


def test_mark_as_read_success(mock_client: Mock) -> None:
    # ARRANGE
    mock_client.mark_as_read.return_value = True
    message_id = "msg_123"

    # ACT
    response = client.post(f"/messages/{message_id}/mark-as-read")

    # ASSERT
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "marked as read"}
    mock_client.mark_as_read.assert_called_once_with(message_id)


def test_mark_as_read_failure(mock_client: Mock) -> None:
    # ARRANGE
    mock_client.mark_as_read.return_value = False
    message_id = "msg_123"

    # ACT
    response = client.post(f"/messages/{message_id}/mark-as-read")

    # ASSERT
    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to mark message as read"}
    mock_client.mark_as_read.assert_called_once_with(message_id)


def test_delete_message_success(mock_client: Mock) -> None:
    # ARRANGE
    mock_client.delete_message.return_value = True

    # ACT
    response = client.delete("/messages/msg-123")

    # ASSERT
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "deleted"}
    mock_client.delete_message.assert_called_once_with("msg-123")


def test_delete_message_failure(mock_client: Mock) -> None:
    # ARRANGE
    mock_client.delete_message.return_value = False

    # ACT
    response = client.delete("/messages/msg-123")

    # ASSERT
    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to delete message"}
    mock_client.delete_message.assert_called_once_with("msg-123")
