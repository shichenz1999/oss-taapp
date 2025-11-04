# claude_chat_impl/tests/test_implementation.py

from unittest.mock import MagicMock

import pytest

# Import what we are testing
from claude_chat_impl.implementation import (
    ClaudeChatImplementation,
    MissingClaudeAPIKeyError,
)
from claude_chat_impl.user_key_store import ClaudeAPIKeyRepository

# Import the contract models
from claude_chat_api import Message, MessageRole


def test_send_message_success(mocker, tmp_path):
    """Tests a successful send_message call by mocking the
    Claude client and using a temporary key repository.
    """
    repo = ClaudeAPIKeyRepository(str(tmp_path / "keys.db"))
    user_id = "test_user_123"
    repo.set_api_key(user_id, "sk-user-123")

    impl = ClaudeChatImplementation(key_repository=repo)

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "This is a mock AI reply."
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response

    mocker.patch.object(impl, "_create_client", return_value=mock_client)

    prompt = "Hello AI"
    response = impl.send_message(prompt, user_id)

    assert isinstance(response, Message)
    assert response.role == MessageRole.ASSISTANT
    assert response.content == "This is a mock AI reply."

    mock_client.messages.create.assert_called_once_with(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        system="You are a helpful assistant.",
        messages=[{"role": "user", "content": prompt}],
    )


def test_send_message_without_registered_key(tmp_path):
    """Users must register a Claude API key before chatting."""
    repo = ClaudeAPIKeyRepository(str(tmp_path / "keys.db"))
    impl = ClaudeChatImplementation(key_repository=repo)

    with pytest.raises(MissingClaudeAPIKeyError):
        impl.send_message("Hello", "unknown-user")
