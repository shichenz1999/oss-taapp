"""Contract tests for the AI chat API abstractions."""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from ai_chat_api import Client, Message

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))



class DummyMessage(Message):
    """Minimal concrete Message implementation for testing."""

    def __init__(self, role: str, content: str) -> None:
        if not isinstance(role, str) or not role:
            error_message = "role must be a non-empty string"
            raise ValueError(error_message)
        self._role = role
        self._content = str(content)

    @property
    def role(self) -> str:
        return self._role

    @property
    def content(self) -> str:
        return self._content


def test_message_model_validates_role() -> None:
    """A Message can be created with a role and content."""
    message = DummyMessage(role="user", content="Hello, AI assistant!")
    assert message.role == "user"
    assert message.content == "Hello, AI assistant!"


def test_message_model_rejects_invalid_role() -> None:
    """The model raises when provided an unsupported role value."""
    with pytest.raises(ValueError, match="non-empty string"):
        DummyMessage(role="", content="nope")


def test_abstract_api_send_message_contract() -> None:
    """Implementations must return assistant messages from send_message."""
    mock_api = Mock(spec=Client)
    mock_api.send_message.return_value = DummyMessage(
        role="assistant",
        content="Here is your AI response.",
    )

    response = mock_api.send_message(prompt="Hello!", user_id="user-123")

    mock_api.send_message.assert_called_once_with(prompt="Hello!", user_id="user-123")
    assert response.role == "assistant"
    assert response.content == "Here is your AI response."


def test_abstract_api_cannot_instantiate_directly() -> None:
    """Abstract classes remain non-instantiable until implemented."""
    with pytest.raises(TypeError):
        Client()
