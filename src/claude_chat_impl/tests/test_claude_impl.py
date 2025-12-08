"""Tests for the Claude AIInterface implementation."""

from unittest.mock import ANY, MagicMock

from ai_chat_api import AIInterface, AIStructuredResponse
from claude_chat_impl.claude_impl import ClaudeClient


def test_generate_response_returns_structured_payload(mocker):
    """generate_response returns an AIStructuredResponse when JSON is requested."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = '{"intent":"create_ticket","message":"Ticket created","parameters":{"title":"mocked"}}'
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response

    mocker.patch("claude_chat_impl.claude_impl.claude_client", mock_client)

    impl: AIInterface = ClaudeClient()
    response = impl.generate_response(
        user_input="Create a ticket please",
        system_prompt="Assist with tickets",
        response_schema={"type": "object"},
    )

    assert isinstance(response, AIStructuredResponse)
    assert response.intent == "create_ticket"
    assert response.message == "Ticket created"
    assert response.parameters["title"] == "mocked"

    mock_client.messages.create.assert_called_once_with(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        system=ANY,
        messages=[{"role": "user", "content": "Create a ticket please"}],
    )
    assert "You must output valid JSON only. No Markdown. No pre-amble." in mock_client.messages.create.call_args.kwargs["system"]


def test_generate_response_allows_plain_text_when_not_json(mocker):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "This is a mock AI reply."
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response
    mocker.patch("claude_chat_impl.claude_impl.claude_client", mock_client)

    impl = ClaudeClient()

    response = impl.generate_response(
        user_input="Hello AI",
        system_prompt="Be concise",
        response_schema=None,
    )

    assert isinstance(response, str)
    assert response == "This is a mock AI reply."
