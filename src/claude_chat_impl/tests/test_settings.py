"""Tests for the AppSettings configuration."""

from claude_chat_impl.settings import AppSettings


def test_app_settings_populates_from_environment(monkeypatch) -> None:
    """AppSettings should read required environment variables."""
    monkeypatch.setenv("CLAUDE_API_KEY", "override-key")

    settings = AppSettings()

    assert settings.CLAUDE_API_KEY == "override-key"
