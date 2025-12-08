# claude_chat_impl/src/claude_chat_impl/claude_impl.py
"""Anthropic-backed implementation of the ai_chat_api.AIInterface contract."""

from __future__ import annotations

import json
from typing import Any

import anthropic

import ai_chat_api
from ai_chat_api import AIInterface, AIStructuredResponse

from .settings import settings

claude_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def _should_request_json(response_schema: dict[str, Any] | None) -> bool:
    """Determine whether we should coerce Claude to emit JSON."""
    return response_schema is not None


def _format_system_prompt(
    system_prompt: str,
    require_json: bool,
    response_schema: dict[str, Any] | None,
) -> str:
    """Append JSON-formatting guidance and any supplied schema to the system prompt."""
    sections = [system_prompt]
    if response_schema:
        schema_text = json.dumps(response_schema)
        sections.append(f"Use the following JSON schema for your reply: {schema_text}")
    if require_json:
        sections.append("You must output valid JSON only. No Markdown. No pre-amble.")
    return "\n".join(sections)


class ClaudeClient(AIInterface):
    """Concrete chat client that proxies calls to Anthropic's Claude API."""

    def generate_response(
        self,
        user_input: str,
        system_prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> str | AIStructuredResponse:
        """Send a prompt and return either free text or a structured response."""
        require_json = _should_request_json(response_schema)
        formatted_prompt = _format_system_prompt(system_prompt, require_json, response_schema)

        api_response: Any = claude_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            system=formatted_prompt,
            messages=[{"role": "user", "content": user_input}],
        )

        text_response = api_response.content[0].text
        if not require_json:
            return text_response

        return self._parse_structured_response(text_response)

    def _parse_structured_response(self, text_response: str) -> AIStructuredResponse:
        """Convert Claude JSON output into an AIStructuredResponse."""
        try:
            return AIStructuredResponse.model_validate_json(text_response)
        except Exception:
            try:
                payload = json.loads(text_response)
            except json.JSONDecodeError as exc:  # pragma: no cover - defensive path
                error_message = f"Claude did not return valid JSON: {text_response!r}"
                raise ValueError(error_message) from exc
            return AIStructuredResponse.model_validate(payload)


def get_ai_interface_impl() -> ClaudeClient:
    """Return a new ClaudeClient instance."""
    return ClaudeClient()


def register() -> None:
    """Register the Claude client factory with the ai_chat_api contract."""
    ai_chat_api.get_ai_interface = get_ai_interface_impl
