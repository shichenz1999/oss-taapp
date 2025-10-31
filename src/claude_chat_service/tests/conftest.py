"""Shared fixtures for claude_chat_service tests."""

import os


DEFAULT_ENV = {
    "CLAUDE_API_KEY": "test-claude-key",
    "OAUTH_CLIENT_ID": "test-client-id",
    "OAUTH_CLIENT_SECRET": "test-client-secret",
    "SESSION_SECRET_KEY": "test-session-secret",
}


for key, value in DEFAULT_ENV.items():
    os.environ.setdefault(key, value)
