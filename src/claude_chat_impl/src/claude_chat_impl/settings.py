# claude_chat_impl/src/claude_chat_impl/settings.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    ANTHROPIC_API_KEY: str
    OAUTH_CLIENT_ID: str
    OAUTH_CLIENT_SECRET: str
    OAUTH_REDIRECT_URI: str = "http://127.0.0.1:8000/auth/callback"
    OAUTH_AUTH_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
    OAUTH_TOKEN_URL: str = "https://oauth2.googleapis.com/token"
    OAUTH_USERINFO_URL: str = "https://www.googleapis.com/oauth2/v1/userinfo"
    SESSION_SECRET_KEY: str
    SESSION_ALGORITHM: str = "HS256"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = AppSettings()
