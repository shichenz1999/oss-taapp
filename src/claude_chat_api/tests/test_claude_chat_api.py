"""Contract tests for the Claude chat API abstractions."""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import ValidationError
from claude_chat_api import AbstractClaudeChatAPI, Message, MessageRole

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))



def test_message_role_values() -> None:
    """The message role enum exposes user and assistant labels."""
    assert MessageRole.USER.value == "user"
    assert MessageRole.ASSISTANT.value == "assistant"


def test_message_model_validates_role() -> None:
    """A Message can be created from the strongly typed role."""
    message = Message(role=MessageRole.USER, content="Hello, Claude!")
    assert message.role is MessageRole.USER
    assert message.content == "Hello, Claude!"


def test_message_model_rejects_invalid_role() -> None:
    """The model raises when provided an unsupported role value."""
    with pytest.raises(ValidationError):
        Message(role="system", content="nope")  # type: ignore[arg-type]


def test_abstract_api_send_message_contract() -> None:
    """Implementations must return assistant messages from send_message."""
    mock_api = Mock(spec=AbstractClaudeChatAPI)
    mock_api.send_message.return_value = Message(
        role=MessageRole.ASSISTANT,
        content="Here is your Claude response.",
    )

    response = mock_api.send_message(prompt="Hello!", user_id="user-123")

    mock_api.send_message.assert_called_once_with(prompt="Hello!", user_id="user-123")
    assert response.role is MessageRole.ASSISTANT
    assert response.content == "Here is your Claude response."


def test_abstract_api_cannot_instantiate_directly() -> None:
    """Abstract classes remain non-instantiable until implemented."""
    with pytest.raises(TypeError):
        AbstractClaudeChatAPI()
