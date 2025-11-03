"""Tests for the OAuth authorization flow managed by AuthManager."""

from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from pytest_mock import MockerFixture

from claude_chat_impl.auth_manager import AuthManager


def _stub_settings() -> SimpleNamespace:
    return SimpleNamespace(
        OAUTH_AUTH_URL="https://accounts.example.com/o/oauth2/v2/auth",
        OAUTH_CLIENT_ID="client-123",
        OAUTH_CLIENT_SECRET="secret-xyz",
        OAUTH_REDIRECT_URI="https://app.example.com/auth/callback",
        OAUTH_TOKEN_URL="https://accounts.example.com/token",
        OAUTH_USERINFO_URL="https://accounts.example.com/userinfo",
    )


def test_get_authorization_url_builds_expected_query(mocker: MockerFixture) -> None:
    """The authorization URL must include the required OAuth parameters."""
    mocker.patch("claude_chat_impl.auth_manager.settings", _stub_settings())

    manager = AuthManager()
    url = manager.get_authorization_url()

    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "accounts.example.com"

    params = parse_qs(parsed.query)
    assert params["response_type"] == ["code"]
    assert params["client_id"] == ["client-123"]
    assert params["redirect_uri"] == ["https://app.example.com/auth/callback"]
    assert params["scope"] == ["openid email profile"]
    assert params["access_type"] == ["offline"]


def test_exchange_code_for_tokens_success(mocker: MockerFixture) -> None:
    """Successful code exchange returns the JSON payload from the token endpoint."""
    fake_settings = _stub_settings()
    mocker.patch("claude_chat_impl.auth_manager.settings", fake_settings)

    mock_response = mocker.MagicMock()
    mock_response.json.return_value = {"access_token": "token-abc"}

    mock_client = mocker.MagicMock()
    mock_client.post.return_value = mock_response
    mocker.patch("claude_chat_impl.auth_manager.httpx.Client").return_value.__enter__.return_value = (
        mock_client
    )

    manager = AuthManager()
    tokens = manager.exchange_code_for_tokens("auth-code")

    mock_client.post.assert_called_once_with(
        fake_settings.OAUTH_TOKEN_URL,
        data={
            "code": "auth-code",
            "client_id": fake_settings.OAUTH_CLIENT_ID,
            "client_secret": fake_settings.OAUTH_CLIENT_SECRET,
            "redirect_uri": fake_settings.OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    mock_response.raise_for_status.assert_called_once_with()
    assert tokens == {"access_token": "token-abc"}


def test_exchange_code_for_tokens_propagates_http_error(mocker: MockerFixture) -> None:
    """HTTP errors from the token endpoint are surfaced to the caller."""
    fake_settings = _stub_settings()
    mocker.patch("claude_chat_impl.auth_manager.settings", fake_settings)

    request = httpx.Request("POST", fake_settings.OAUTH_TOKEN_URL)
    response = httpx.Response(400, request=request, text="bad request")
    http_error = httpx.HTTPStatusError("boom", request=request, response=response)

    mock_response = mocker.MagicMock()
    mock_response.raise_for_status.side_effect = http_error
    mock_client = mocker.MagicMock()
    mock_client.post.return_value = mock_response
    mocker.patch("claude_chat_impl.auth_manager.httpx.Client").return_value.__enter__.return_value = (
        mock_client
    )

    manager = AuthManager()
    with pytest.raises(httpx.HTTPStatusError):
        manager.exchange_code_for_tokens("bad-code")


def test_get_user_info_returns_profile_payload(mocker: MockerFixture) -> None:
    """The user info request forwards the bearer token and returns the JSON response."""
    fake_settings = _stub_settings()
    mocker.patch("claude_chat_impl.auth_manager.settings", fake_settings)

    mock_response = mocker.MagicMock()
    mock_response.json.return_value = {"email": "user@example.com"}
    mock_client = mocker.MagicMock()
    mock_client.get.return_value = mock_response
    mocker.patch("claude_chat_impl.auth_manager.httpx.Client").return_value.__enter__.return_value = (
        mock_client
    )

    manager = AuthManager()
    profile = manager.get_user_info("token-abc")

    mock_client.get.assert_called_once_with(
        fake_settings.OAUTH_USERINFO_URL,
        headers={"Authorization": "Bearer token-abc"},
    )
    mock_response.raise_for_status.assert_called_once_with()
    assert profile == {"email": "user@example.com"}


def test_get_user_info_propagates_http_error(mocker: MockerFixture) -> None:
    """Errors from the userinfo endpoint bubble up for the caller to handle."""
    fake_settings = _stub_settings()
    mocker.patch("claude_chat_impl.auth_manager.settings", fake_settings)

    request = httpx.Request("GET", fake_settings.OAUTH_USERINFO_URL)
    response = httpx.Response(500, request=request, text="server error")
    http_error = httpx.HTTPStatusError("failed", request=request, response=response)

    mock_response = mocker.MagicMock()
    mock_response.raise_for_status.side_effect = http_error
    mock_client = mocker.MagicMock()
    mock_client.get.return_value = mock_response
    mocker.patch("claude_chat_impl.auth_manager.httpx.Client").return_value.__enter__.return_value = (
        mock_client
    )

    manager = AuthManager()
    with pytest.raises(httpx.HTTPStatusError):
        manager.get_user_info("token-abc")
