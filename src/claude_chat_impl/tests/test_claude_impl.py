"""Tests for the Claude AI interface implementation."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from claude_chat_impl.claude_impl import ClaudeAIInterface, get_ai_interface_impl, register


def _build_mock_response(text: str) -> MagicMock:
    mock_content = MagicMock()
    mock_content.text = text
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    return mock_response


def test_generate_response_returns_text(mocker: Any) -> None:
    """Plain prompts return string responses."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _build_mock_response("Mock reply")
    mocker.patch("claude_chat_impl.claude_impl.claude_client", mock_client)

    interface = ClaudeAIInterface()
    result = interface.generate_response(user_input="Hello Claude")

    assert result == "Mock reply"
    mock_client.messages.create.assert_called_once()
    assert mock_client.messages.create.call_args.kwargs == {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": "Hello Claude"}],
    }


def test_generate_response_returns_structured_payload(mocker: Any) -> None:
    """Providing a schema yields parsed JSON."""
    schema = {"type": "object", "properties": {"summary": {"type": "string"}}}
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _build_mock_response('{"summary": "done"}')
    mocker.patch("claude_chat_impl.claude_impl.claude_client", mock_client)

    interface = ClaudeAIInterface()
    result = interface.generate_response(
        user_input="Summarise the meeting",
        system_prompt="Summariser",
        response_schema=schema,
    )

    assert result == {"summary": "done"}
    called_kwargs = mock_client.messages.create.call_args.kwargs
    assert "Summariser" in (called_kwargs["system"] or "")
    assert json.dumps(schema) in (called_kwargs["system"] or "")


def test_generate_response_raises_on_invalid_json(mocker: Any) -> None:
    """Invalid JSON responses raise a descriptive error."""
    schema = {"type": "object", "properties": {"summary": {"type": "string"}}}
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _build_mock_response("not-json")
    mocker.patch("claude_chat_impl.claude_impl.claude_client", mock_client)

    interface = ClaudeAIInterface()

    with pytest.raises(ValueError, match="invalid JSON"):
        interface.generate_response(
            user_input="Summarise",
            response_schema=schema,
        )


def test_get_ai_interface_impl_returns_new_instance() -> None:
    """Factory helper returns ClaudeAIInterface instances."""
    implementation = get_ai_interface_impl()

    assert isinstance(implementation, ClaudeAIInterface)


def test_register_binds_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Register function rebinds ai_chat_api.get_ai_interface."""
    import ai_chat_api

    sentinel = object()
    monkeypatch.setattr(ai_chat_api, "get_ai_interface", sentinel, raising=False)

    register()

    assert ai_chat_api.get_ai_interface is get_ai_interface_impl
