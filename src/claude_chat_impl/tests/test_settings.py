"""Tests for the AppSettings configuration."""

from claude_chat_impl.settings import AppSettings


def test_app_settings_populates_from_environment(monkeypatch) -> None:
    """AppSettings should read required environment variables."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "override-key")

    settings = AppSettings(_env_file=None)

    assert settings.ANTHROPIC_API_KEY == "override-key"
