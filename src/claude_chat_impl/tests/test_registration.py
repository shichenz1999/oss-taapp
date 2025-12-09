"""Registration-focused tests for the Claude implementation package."""

from __future__ import annotations

import importlib
import sys

import ai_chat_api
import pytest


def test_import_registers_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Importing the package binds ai_chat_api.get_ai_interface."""
    previous_factory = ai_chat_api.get_ai_interface
    monkeypatch.setattr(ai_chat_api, "get_ai_interface", previous_factory, raising=False)

    if "claude_chat_impl" in sys.modules:
        del sys.modules["claude_chat_impl"]

    module = importlib.import_module("claude_chat_impl")

    try:
        assert ai_chat_api.get_ai_interface is module.get_ai_interface_impl
    finally:
        ai_chat_api.get_ai_interface = previous_factory
