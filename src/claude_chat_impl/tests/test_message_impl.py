"""Tests for the Claude message implementation helpers."""

from types import SimpleNamespace

import ai_chat_api

from claude_chat_impl.message_impl import (
    ClaudeMessage,
    anthropic_response_to_message,
    get_message_impl,
    register,
)


def test_claude_message_properties() -> None:
    message = ClaudeMessage(role="assistant", content="Hello")

    assert message.role == "assistant"
    assert message.content == "Hello"


def test_anthropic_response_to_message_converts_payload() -> None:
    response = SimpleNamespace(
        role="assistant",
        content=[SimpleNamespace(text="Converted")],
    )

    message = anthropic_response_to_message(response)

    assert isinstance(message, ClaudeMessage)
    assert message.role == "assistant"
    assert message.content == "Converted"


def test_get_message_impl_returns_claude_message() -> None:
    message = get_message_impl(role="assistant", content="Hi")

    assert isinstance(message, ClaudeMessage)
    assert message.role == "assistant"
    assert message.content == "Hi"


def test_register_binds_factory(monkeypatch) -> None:
    sentinel = object()
    monkeypatch.setattr(ai_chat_api, "get_message", sentinel, raising=False)

    register()

    assert ai_chat_api.get_message is get_message_impl
