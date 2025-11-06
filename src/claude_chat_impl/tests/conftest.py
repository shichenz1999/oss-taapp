"""Shared pytest fixtures for the claude_chat_impl test suite."""

import os

_DEFAULT_ENV = {
    "ANTHROPIC_API_KEY": "test-claude-key",
    "OAUTH_CLIENT_ID": "test-client-id",
    "OAUTH_CLIENT_SECRET": "test-client-secret",
    "SESSION_SECRET_KEY": "test-session-secret",
}


for key, value in _DEFAULT_ENV.items():
    os.environ.setdefault(key, value)
