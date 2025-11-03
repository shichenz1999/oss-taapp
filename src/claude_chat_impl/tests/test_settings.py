"""Tests for the AppSettings configuration."""

from pytest import MonkeyPatch

from claude_chat_impl.settings import AppSettings


def test_app_settings_populates_from_environment(monkeypatch: MonkeyPatch) -> None:
    """AppSettings should read required environment variables."""
    monkeypatch.setenv("CLAUDE_API_KEY", "override-key")
    monkeypatch.setenv("OAUTH_CLIENT_ID", "override-client")
    monkeypatch.setenv("OAUTH_CLIENT_SECRET", "override-secret")
    monkeypatch.setenv("SESSION_SECRET_KEY", "override-session")

    settings = AppSettings()  # type: ignore[call-arg]

    assert settings.CLAUDE_API_KEY == "override-key"
    assert settings.OAUTH_CLIENT_ID == "override-client"
    assert settings.OAUTH_CLIENT_SECRET == "override-secret"
    assert settings.SESSION_SECRET_KEY == "override-session"
