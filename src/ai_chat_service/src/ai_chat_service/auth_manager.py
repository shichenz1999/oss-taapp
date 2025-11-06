# ai_chat_service/src/ai_chat_service/auth_manager.py

"""OAuth 2.0 helpers for the AI chat FastAPI service."""

from typing import Any

import httpx

from .settings import settings


class AuthManager:
    """Utility class that handles the OAuth 2.0 Authorization Code flow."""

    def get_authorization_url(self) -> str:
        """Return the external provider's authorization URL."""
        params = {
            "response_type": "code",
            "client_id": settings.OAUTH_CLIENT_ID,
            "redirect_uri": settings.OAUTH_REDIRECT_URI,
            "scope": "openid email profile",
            "access_type": "offline",
        }
        query = "&".join(f"{key}={value}" for key, value in params.items())
        return f"{settings.OAUTH_AUTH_URL}?{query}"

    def exchange_code_for_tokens(self, code: str) -> dict[str, Any]:
        """Exchange the authorization code for access/refresh tokens."""
        data = {
            "code": code,
            "client_id": settings.OAUTH_CLIENT_ID,
            "client_secret": settings.OAUTH_CLIENT_SECRET,
            "redirect_uri": settings.OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        with httpx.Client() as client:
            response = client.post(settings.OAUTH_TOKEN_URL, data=data)
            response.raise_for_status()
            return response.json()

    def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Fetch user profile data using the provided access token."""
        headers = {"Authorization": f"Bearer {access_token}"}
        with httpx.Client() as client:
            response = client.get(settings.OAUTH_USERINFO_URL, headers=headers)
            response.raise_for_status()
            return response.json()
