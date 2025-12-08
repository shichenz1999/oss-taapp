"""Contract tests for the AI chat API abstractions."""

import sys
from pathlib import Path

import pytest
from ai_chat_api import AIInterface, AIStructuredResponse

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))


class DummyAI(AIInterface):
    """Minimal AI implementation for exercising the contract."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, object] | None]] = []

    def generate_response(
        self,
        user_input: str,
        system_prompt: str,
        response_schema: dict[str, object] | None = None,
    ) -> str | AIStructuredResponse:
        self.calls.append((user_input, system_prompt, response_schema))
        if response_schema is not None:
            return AIStructuredResponse(intent="ticket.create", parameters={"title": user_input})
        return f"{system_prompt}: {user_input}"


def test_structured_response_model_round_trips() -> None:
    """Structured model preserves intent and parameters."""
    response = AIStructuredResponse(intent="ticket.update", parameters={"id": 42, "status": "open"})

    assert response.intent == "ticket.update"
    assert response.parameters["id"] == 42
    assert response.parameters["status"] == "open"


def test_generate_response_contract_accepts_schema() -> None:
    """Implementations surface either a string or AIStructuredResponse."""
    ai = DummyAI()
    schema = {"type": "object"}

    result = ai.generate_response(user_input="hello", system_prompt="assist", response_schema=schema)

    assert isinstance(result, AIStructuredResponse)
    assert result.intent == "ticket.create"
    assert ai.calls == [("hello", "assist", schema)]


def test_generate_response_can_return_string() -> None:
    ai = DummyAI()

    result = ai.generate_response(user_input="hello", system_prompt="assist")

    assert isinstance(result, str)
    assert "assist" in result


def test_abstract_api_cannot_instantiate_directly() -> None:
    """Abstract classes remain non-instantiable until implemented."""
    with pytest.raises(TypeError):
        AIInterface()  # type: ignore[abstract]
