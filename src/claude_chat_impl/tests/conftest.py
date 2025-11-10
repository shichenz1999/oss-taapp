# ruff: noqa: INP001
"""Shared pytest fixtures for the claude_chat_impl test suite."""

import os

_DEFAULT_ENV = {
    "ANTHROPIC_API_KEY": "test-claude-key",
}


for key, value in _DEFAULT_ENV.items():
    os.environ.setdefault(key, value)
