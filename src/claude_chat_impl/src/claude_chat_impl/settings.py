"""Configuration objects shared by the Claude chat implementation."""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

LOGGER = logging.getLogger(__name__)


def _resolve_env_files() -> tuple[str, ...]:
    """Return candidate .env files by walking up the directory tree."""
    candidates: list[str] = []
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".env"
        if candidate.exists():
            candidates.append(str(candidate))
    candidates.append(".env")
    seen: set[str] = set()
    ordered: list[str] = []
    for item in candidates:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return tuple(ordered)


class AppSettings(BaseSettings):
    """Manage all application settings and secrets."""

    CLAUDE_API_KEY: str
    OAUTH_CLIENT_ID: str
    OAUTH_CLIENT_SECRET: str
    OAUTH_REDIRECT_URI: str = "http://127.0.0.1:8000/auth/callback"
    OAUTH_AUTH_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
    OAUTH_TOKEN_URL: str = "https://oauth2.googleapis.com/token"  # noqa: S105
    OAUTH_USERINFO_URL: str = "https://www.googleapis.com/oauth2/v1/userinfo"
    SESSION_SECRET_KEY: str
    SESSION_ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(
        env_file=_resolve_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )


try:
    settings = AppSettings()  # type: ignore[call-arg]
except Exception:
    LOGGER.exception("Error loading settings. Ensure a .env file exists.")
    raise
