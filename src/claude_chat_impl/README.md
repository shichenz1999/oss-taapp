# Claude Chat Implementation

## Overview
`claude_chat_impl` supplies the Anthropic-backed implementation of the
`ai_chat_api.AIInterface` contract. Importing the package registers Claude as
the active AI interface so services can call Anthropic without touching the SDK.

## Responsibilities
- Expose `ClaudeAIInterface`, an `AIInterface` implementation that wraps
  `anthropic.Anthropic`.
- Register `get_ai_interface_impl` as the active `ai_chat_api.get_ai_interface`
  factory on import.
- Provide strongly typed settings so the Anthropic API key is sourced from a
  single place.

## Key Modules
```
claude_chat_impl/
├── README.md                                # Package guide (this file)
├── pyproject.toml                           # Build metadata and dependencies
├── src/claude_chat_impl/
│   ├── __init__.py                          # Public exports + auto-registration hook
│   ├── claude_impl.py                       # ClaudeAIInterface + factory registration
│   └── settings.py                          # Pydantic settings sourced from environment
└── tests/
    ├── conftest.py                          # Shared fixtures for patched SDK calls
    ├── test_claude_impl.py                  # Validates interface behaviour
    └── test_settings.py                     # Ensures settings load from environment safely
```

- `__init__.py` – Exports the primary surface and runs `register()` so
  `ai_chat_api.get_ai_interface` points to Claude by default.
- `claude_impl.py` – Wraps `anthropic.Anthropic`, adds structured-response
  directives when schemas are provided, and parses the resulting JSON payloads.
- `settings.py` – Centralised configuration powered by `pydantic-settings`
  that loads `ANTHROPIC_API_KEY` from the environment.

## Environment Configuration
Set the following variable (or place it inside a `.env` file) so `AppSettings`
can hydrate correctly:

- `ANTHROPIC_API_KEY` – Claude API key used to authenticate with Anthropic.

## Usage
```python
import claude_chat_impl  # registers the Claude implementation
from ai_chat_api import get_ai_interface

ai = get_ai_interface()
response = ai.generate_response(
    user_input="Summarise the syllabus",
    system_prompt="You are a helpful tutor",
)
print(response)
```

Pass a JSON schema when you need structured output:

```python
schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "next_action": {"type": "string"},
    },
}

structured = ai.generate_response(
    user_input="Outline tomorrow's work",
    system_prompt="Project planner",
    response_schema=schema,
)
print(structured["summary"])
```

## Testing
```bash
uv run pytest src/claude_chat_impl/tests -q
```

The suite patches Anthropic interactions to keep runs deterministic while
exercising registration, structured-response handling, and configuration logic.
