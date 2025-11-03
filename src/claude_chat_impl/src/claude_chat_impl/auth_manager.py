
"""OAuth helper responsible for the Google authorization code flow."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

import httpx

from .settings import settings

if TYPE_CHECKING:
    from collections.abc import Mapping

LOGGER = logging.getLogger(__name__)


class AuthManager:
    """Handle the OAuth 2.0 Authorization Code Flow."""

    def get_authorization_url(self) -> str:
        """Generate the provider login URL to initiate the flow."""
        scope = "openid email profile"
        return (
            f"{settings.OAUTH_AUTH_URL}?"
            f"response_type=code&"
            f"client_id={settings.OAUTH_CLIENT_ID}&"
            f"redirect_uri={settings.OAUTH_REDIRECT_URI}&"
            f"scope={scope}&"
            f"access_type=offline"
        )

    def exchange_code_for_tokens(self, code: str) -> Mapping[str, object]:
        """Exchange the authorization code for access and refresh tokens."""
        token_request_data = {
            "code": code,
            "client_id": settings.OAUTH_CLIENT_ID,
            "client_secret": settings.OAUTH_CLIENT_SECRET,
            "redirect_uri": settings.OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        with httpx.Client() as client:
            try:
                response = client.post(settings.OAUTH_TOKEN_URL, data=token_request_data)
                response.raise_for_status()
                return cast("Mapping[str, object]", response.json())
            except httpx.HTTPStatusError as exc:
                LOGGER.exception("Token exchange failed: %s", exc.response.text)
                raise

    def get_user_info(self, access_token: str) -> Mapping[str, object]:
        """Fetch the authenticated user's profile from the provider."""
        headers = {"Authorization": f"Bearer {access_token}"}

        with httpx.Client() as client:
            try:
                response = client.get(settings.OAUTH_USERINFO_URL, headers=headers)
                response.raise_for_status()
                return cast("Mapping[str, object]", response.json())
            except httpx.HTTPStatusError as exc:
                LOGGER.exception("Failed to get user info: %s", exc.response.text)
                raise
