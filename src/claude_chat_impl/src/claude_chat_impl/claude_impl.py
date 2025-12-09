"""Anthropic-backed implementation of the ai_chat_api.AIInterface contract."""
from __future__ import annotations

import json
from typing import Any, Dict

import anthropic

import ai_chat_api
from ai_chat_api import AIInterface

from .settings import settings

claude_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


class ClaudeAIInterface(AIInterface):
    """Concrete AIInterface implementation that wraps Anthropic's Claude API."""

    def generate_response(
        self,
        user_input: str,
        system_prompt: str | None = None,
        response_schema: Dict[str, Any] | None = None,
    ) -> str | Dict[str, Any]:
        """Invoke Claude and return raw text or structured JSON."""
        directives: list[str] = []
        if system_prompt:
            directives.append(system_prompt.strip())

        if response_schema is not None:
            directives.append(
                "You must return JSON that strictly conforms to the following schema:\n"
                f"{json.dumps(response_schema)}\n"
                "Do not include any extra text—only valid JSON."
            )

        system_text = "\n\n".join(directives) if directives else None

        messages = [
            {"role": "user", "content": user_input}
        ]

        request_kwargs: dict[str, Any] = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1024,
            "messages": messages,
        }
        if system_text is not None:
            request_kwargs["system"] = system_text

        api_response = claude_client.messages.create(**request_kwargs)

        content = api_response.content[0].text.strip()
        if response_schema is None:
            return content

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("Claude returned invalid JSON for the provided schema") from exc


def get_ai_interface_impl() -> ClaudeAIInterface:
    """Return a ClaudeAIInterface instance."""
    return ClaudeAIInterface()


def register() -> None:
    """Register the Claude AI interface factory with ai_chat_api."""
    ai_chat_api.get_ai_interface = get_ai_interface_impl
