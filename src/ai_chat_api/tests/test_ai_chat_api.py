"""Contract tests for the AI chat API abstractions."""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from ai_chat_api import AIInterface

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))


class DummyAIInterface(AIInterface):
    """Concrete helper used to validate the AIInterface abstraction."""

    def generate_response(
        self,
        user_input: str,
        system_prompt: str | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> str | dict[str, Any]:
        if response_schema is None:
            prefix = system_prompt.strip() if system_prompt else "assistant"
            return f"{prefix}: {user_input}"

        properties = response_schema.get("properties", {})
        return {name: user_input for name in properties}


def test_generate_response_returns_text_without_schema() -> None:
    """Implementations can return plain strings for conversational replies."""
    interface = DummyAIInterface()

    response = interface.generate_response(user_input="Hello!", system_prompt="Be helpful")

    assert isinstance(response, str)
    assert "Hello!" in response
    assert "Be helpful" in response


def test_generate_response_returns_structured_data_with_schema() -> None:
    """Implementations can emit structured payloads when given a schema."""
    interface = DummyAIInterface()
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "next_action": {"type": "string"},
        },
    }

    response = interface.generate_response(
        user_input="Observe the lab results.",
        system_prompt="Planner",
        response_schema=schema,
    )

    assert isinstance(response, dict)
    assert set(response.keys()) == {"summary", "next_action"}
    assert response["summary"] == "Observe the lab results."


def test_generate_response_handles_missing_system_prompt() -> None:
    """System prompt is optional and defaults to a sensible prefix."""
    interface = DummyAIInterface()

    response = interface.generate_response(user_input="Status update?", system_prompt=None)

    assert response.startswith("assistant:")
    assert "Status update?" in response


def test_generate_response_contract_invocation() -> None:
    """Consumers call generate_response with the expected signature."""
    mock_interface = Mock(spec=AIInterface)
    mock_interface.generate_response.return_value = "Acknowledged"
    schema = {"type": "object", "properties": {"summary": {"type": "string"}}}

    result = mock_interface.generate_response(
        user_input="Draft a memo",
        system_prompt="Corporate assistant",
        response_schema=schema,
    )

    mock_interface.generate_response.assert_called_once_with(
        user_input="Draft a memo",
        system_prompt="Corporate assistant",
        response_schema=schema,
    )
    assert result == "Acknowledged"


def test_ai_interface_cannot_instantiate_directly() -> None:
    """Abstract classes remain non-instantiable until implemented."""
    with pytest.raises(TypeError):
        AIInterface()  # type: ignore[abstract]
