# claude_chat_impl/src/claude_chat_impl/settings.py

"""Configuration for the Claude chat implementation."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Environment-driven settings for the Claude integration."""

    CLAUDE_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = AppSettings()
