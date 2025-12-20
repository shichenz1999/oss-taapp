"""Tests for the AppSettings configuration."""

import pytest

from claude_chat_impl.settings import AppSettings


def test_app_settings_populates_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """AppSettings should read required environment variables."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "override-key")

    settings = AppSettings()

    assert settings.ANTHROPIC_API_KEY == "override-key"
