# claude_chat_impl/tests/test_implementation.py

from unittest.mock import MagicMock

# Import what we are testing
from claude_chat_impl.implementation import ClaudeChatImplementation

# Import the contract models
from claude_chat_api import Message, MessageRole


def test_send_message_success(mocker):
    """Tests a successful send_message call by mocking the
    claude_client.
    """
    # 1. Setup the Mock
    # We need to mock the 'claude_client' object inside the
    # 'implementation' file
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "This is a mock AI reply."
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response

    # This replaces the 'claude_client' in that file with our mock
    mocker.patch("claude_chat_impl.implementation.claude_client", mock_client)

    # 2. Create an instance of our class
    impl = ClaudeChatImplementation()

    # 3. Call the method
    prompt = "Hello AI"
    user_id = "test_user_123"
    response = impl.send_message(prompt, user_id)

    # 4. Assert the results
    # Check that our AI reply was returned
    assert isinstance(response, Message)
    assert response.role == MessageRole.ASSISTANT
    assert response.content == "This is a mock AI reply."

    # Check that the mock client was called correctly
    mock_client.messages.create.assert_called_once_with(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        system="You are a helpful assistant.",
        messages=[{"role": "user", "content": prompt}],
    )
