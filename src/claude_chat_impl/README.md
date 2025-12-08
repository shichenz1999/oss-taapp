# Claude Chat Implementation

## Overview
`claude_chat_impl` supplies the Anthropic-backed implementation of the
`ai_chat_api` contract. Importing the package registers Claude as the active chat
provider so services can call Anthropic without dealing with SDK details.

## Responsibilities
- Register `ClaudeClient` as the current `ai_chat_api.get_ai_interface` factory.
- Convert Anthropic SDK responses into structured `AIStructuredResponse`
  payloads when needed.
- Surface strongly-typed settings so Anthropic secrets are pulled from a
  consistent source.

## Key Modules
```
claude_chat_impl/
├── README.md                                # Package guide (this file)
├── pyproject.toml                           # Build metadata and dependencies
├── src/claude_chat_impl/
│   ├── __init__.py                          # Public exports + auto-registration hook
│   ├── claude_impl.py                       # `ClaudeClient` + factory registration
│   └── settings.py                          # Pydantic settings sourced from environment
└── tests/
    ├── conftest.py                          # Shared fixtures for patched SDK calls
    ├── test_claude_impl.py                  # Validates client behaviour and factory wiring
    └── test_settings.py                     # Ensures settings load from environment safely
```

- `__init__.py` – Exports the key classes and runs `register()` on import so
  `ai_chat_api.get_ai_interface` is immediately bound to Claude.
- `claude_impl.py` – Wraps `anthropic.Anthropic` and defines `ClaudeClient`,
  targeting the `claude-3-haiku-20240307` model with sensible defaults.
- `settings.py` – Centralised environment configuration powered by
  `pydantic-settings`. Reads values from `.env` or the process at runtime.

## Environment Configuration
Provide the following environment variable (or set it in a `.env` file) so
`AppSettings` can hydrate correctly:

- `ANTHROPIC_API_KEY` – Claude API key for calling the Anthropic SDK.

## Usage
```python
import claude_chat_impl  # registers the Claude implementation
from ai_chat_api import get_ai_interface

client = get_ai_interface()
response = client.generate_response(
    user_input="Summarise the syllabus",
    system_prompt="You are a helpful assistant.",
)
print(response)
```

The FastAPI service imports `claude_chat_impl` on startup, ensuring both the
chat client factory is registered automatically. Tests can override
`ai_chat_api.get_ai_interface` as needed for isolated scenarios.

## Testing
```bash
uv run pytest src/claude_chat_impl/tests -q
```

The suite patches Anthropic interactions to keep runs fast and deterministic
while covering the registration, message conversion, and settings logic.
