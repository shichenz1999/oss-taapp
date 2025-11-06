# Claude Chat Implementation

## Overview
`claude_chat_impl` supplies the Anthropic-backed implementation of the
`ai_chat_api` contract. Importing the package registers Claude as the active chat
provider so services can call Anthropic without dealing with SDK details.

## Responsibilities
- Register `ClaudeClient` as the current `ai_chat_api.get_client` factory.
- Convert Anthropic SDK responses into concrete `ai_chat_api.Message`
  instances via `ClaudeMessage`.
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
│   ├── message_impl.py                      # Claude-response translation & message factory
│   └── settings.py                          # Pydantic settings sourced from environment
└── tests/
    ├── conftest.py                          # Shared fixtures for patched SDK calls
    ├── test_claude_impl.py                  # Validates client behaviour and factory wiring
    ├── test_message_impl.py                 # Tests message translation helpers + factory registration
    └── test_settings.py                     # Ensures settings load from environment safely
```

- `__init__.py` – Exports the key classes and runs `register()` on import so
  `ai_chat_api.get_client` / `get_message` are immediately bound to Claude.
- `claude_impl.py` – Wraps `anthropic.Anthropic` and defines `ClaudeClient`,
  targeting the `claude-3-haiku-20240307` model with sensible defaults.
- `message_impl.py` – Contains `ClaudeMessage` and translation helpers to map
  Anthropic SDK responses into the workspace message abstraction.
- `src/claude_chat_impl/tests/test_message_impl.py` – Ensures the translation
  helpers and factory registration behave as expected without touching the SDK.
- `settings.py` – Centralised environment configuration powered by
  `pydantic-settings`. Reads values from `.env` or the process at runtime.

## Environment Configuration
Provide the following environment variable (or set it in a `.env` file) so
`AppSettings` can hydrate correctly:

- `ANTHROPIC_API_KEY` – Claude API key for calling the Anthropic SDK.

## Usage
```python
import claude_chat_impl  # registers the Claude implementation
from ai_chat_api import get_client

client = get_client()
message = client.send_message(prompt="Summarise the syllabus", user_id="student-1")
print(message.content)
```

The FastAPI service imports `claude_chat_impl` on startup, ensuring both the
chat client and message factory are registered automatically. Tests can override
`ai_chat_api.get_client` as needed for isolated scenarios.

## Testing
```bash
uv run pytest src/claude_chat_impl/tests -q
```

The suite patches Anthropic interactions to keep runs fast and deterministic
while covering the registration, message conversion, and settings logic.
