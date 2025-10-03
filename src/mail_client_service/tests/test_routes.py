"""Skeleton tests for mail_client_service routes."""

from collections.abc import Generator
from typing import Any
from unittest.mock import create_autospec

import pytest
from fastapi.testclient import TestClient

import mail_client_api
from mail_client_service import app, get_mail_client


@pytest.fixture
def fake_mail_client() -> Any:
    """Provide a spec'd fake mail client for endpoint tests."""
    return create_autospec(mail_client_api.Client)


@pytest.fixture
def api_client(fake_mail_client: mail_client_api.Client) -> Generator[TestClient, None, None]:
    """Yield a TestClient with the mail client dependency overridden."""
    app.dependency_overrides[get_mail_client] = lambda: fake_mail_client
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_mail_client, None)


def test_list_messages_skeleton(api_client: TestClient) -> None:
    pytest.skip("Implement GET /messages test")


def test_get_message_skeleton(api_client: TestClient) -> None:
    pytest.skip("Implement GET /messages/{message_id} test")


def test_mark_as_read_skeleton(api_client: TestClient) -> None:
    pytest.skip("Implement POST /messages/{message_id}/mark-as-read test")


def test_delete_message_success(
    api_client: TestClient,
    fake_mail_client: mail_client_api.Client,
) -> None:
    fake_mail_client.delete_message.return_value = True

    response = api_client.delete("/messages/msg-123")

    assert response.status_code == 200
    assert response.json() == {"status": "deleted"}
    fake_mail_client.delete_message.assert_called_once_with("msg-123")


def test_delete_message_failure(
    api_client: TestClient,
    fake_mail_client: mail_client_api.Client,
) -> None:
    fake_mail_client.delete_message.return_value = False

    response = api_client.delete("/messages/msg-123")

    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to delete message"}
    fake_mail_client.delete_message.assert_called_once_with("msg-123")
