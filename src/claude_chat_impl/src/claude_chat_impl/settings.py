# claude_chat_impl/src/claude_chat_impl/settings.py

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _resolve_env_files() -> tuple[str, ...]:
    """Return candidate .env files by walking up the directory tree."""
    candidates: list[str] = []
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".env"
        if candidate.exists():
            candidates.append(str(candidate))
    candidates.append(".env")
    # Deduplicate while preserving order.
    unique: list[str] = []
    for item in candidates:
        if item not in unique:
            unique.append(item)
    return tuple(unique)


class AppSettings(BaseSettings):
    """Manages all application settings and secrets.
    It reads values from environment variables or a .env file.

    The .env file is expected to be in the monorepo root,
    one level above this component's directory.
    """

    # 1. Claude (Anthropic) API Key
    CLAUDE_API_KEY: str = Field(..., env="CLAUDE_API_KEY")

    # 2. OAuth 2.0 (e.g., Google) Credentials
    OAUTH_CLIENT_ID: str = Field(..., env="OAUTH_CLIENT_ID")
    OAUTH_CLIENT_SECRET: str = Field(..., env="OAUTH_CLIENT_SECRET")
    OAUTH_REDIRECT_URI: str = "http://127.0.0.1:8000/auth/callback"

    # 3. OAuth 2.0 Provider URLs (Example using Google)
    OAUTH_AUTH_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
    OAUTH_TOKEN_URL: str = "https://oauth2.googleapis.com/token"
    OAUTH_USERINFO_URL: str = "https://www.googleapis.com/oauth2/v1/userinfo"

    # 4. JWT Session Token Configuration
    SESSION_SECRET_KEY: str = Field(..., env="SESSION_SECRET_KEY")
    SESSION_ALGORITHM: str = "HS256"

    # Configure pydantic-settings to read from a .env file
    model_config = SettingsConfigDict(
        env_file=_resolve_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Create a single, globally accessible instance of the settings.
try:
    settings = AppSettings()
except Exception as e:
    print(f"Error loading settings: {e}. Make sure a .env file exists.")
    raise
