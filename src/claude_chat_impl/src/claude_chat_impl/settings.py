# claude_chat_impl/src/claude_chat_impl/settings.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    ANTHROPIC_API_KEY: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = AppSettings()
