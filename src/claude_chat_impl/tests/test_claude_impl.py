# claude_chat_impl/tests/test_claude_impl.py

from unittest.mock import MagicMock

# Import what we are testing
from claude_chat_impl.claude_impl import ClaudeClient

# Import the contract models
from ai_chat_api import Message


def test_send_message_success(mocker):
    """Send_message returns an ai_chat_api.Message populated from Anthropic output."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "This is a mock AI reply."
    mock_response.content = [mock_content]
    mock_response.role = "assistant"
    mock_client.messages.create.return_value = mock_response

    # This replaces the 'claude_client' in that file with our mock
    mocker.patch("claude_chat_impl.claude_impl.claude_client", mock_client)

    # 2. Create an instance of our class
    impl = ClaudeClient()

    # 3. Call the method
    prompt = "Hello AI"
    user_id = "test_user_123"
    response = impl.send_message(prompt, user_id)

    # 4. Assert the results
    # Check that our AI reply was returned
    assert isinstance(response, Message)
    assert response.role == "assistant"
    assert response.content == "This is a mock AI reply."

    # Check that the mock client was called correctly
    mock_client.messages.create.assert_called_once_with(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
