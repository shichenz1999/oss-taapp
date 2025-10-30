# claude_chat_impl/src/claude_chat_impl/auth_manager.py

import httpx
from typing import Dict, Any

# Import our centralized settings
from .settings import settings

class AuthManager:
    """
    Handles all logic related to the OAuth 2.0 Authorization Code Flow.
    This class is pure business logic, independent of the web framework.
    """

    def get_authorization_url(self) -> str:
        """
        Generates the URL to which the user must be redirected to
        log in with the external provider (e.g., Google).
        """
        scope = "openid email profile"
        
        auth_url = (
            f"{settings.OAUTH_AUTH_URL}?"
            f"response_type=code&"
            f"client_id={settings.OAUTH_CLIENT_ID}&"
            f"redirect_uri={settings.OAUTH_REDIRECT_URI}&"
            f"scope={scope}&"
            f"access_type=offline"
        )
        return auth_url

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Handles the /auth/callback step.
        Exchanges the temporary 'code' for an 'access_token'.
        This is a synchronous, server-to-server request.
        """
        token_request_data = {
            "code": code,
            "client_id": settings.OAUTH_CLIENT_ID,
            "client_secret": settings.OAUTH_CLIENT_SECRET,
            "redirect_uri": settings.OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        # Use httpx to make the POST request
        # 'with' ensures the client is closed properly
        with httpx.Client() as client:
            try:
                response = client.post(
                    settings.OAUTH_TOKEN_URL, 
                    data=token_request_data
                )
                response.raise_for_status() # Raises on 4xx/5xx
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"Token exchange failed: {e.response.text}")
                raise

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Uses the 'access_token' to fetch the user's profile information
        from the provider's userinfo endpoint.
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        
        with httpx.Client() as client:
            try:
                response = client.get(
                    settings.OAUTH_USERINFO_URL, 
                    headers=headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"Failed to get user info: {e.response.text}")
                raise