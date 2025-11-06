# Claude Chat Implementation

## Overview
`claude_chat_impl` supplies the Anthropic-backed implementation of the
`ai_chat_api` contract and the accompanying OAuth utilities required by
`ai_chat_service`. Importing the package registers Claude as the active chat
provider and exposes helpers for Google OAuth 2.0 flows.

## Responsibilities
- Register `ClaudeClient` as the current `ai_chat_api.get_client` factory.
- Convert Anthropic SDK responses into concrete `ai_chat_api.Message`
  instances via `ClaudeMessage`.
- Provide the `AuthManager` used by the FastAPI service to drive the OAuth
  authorization code flow.
- Surface strongly-typed settings so secrets and OAuth metadata come from a
  consistent source.

## Key Modules
```
claude_chat_impl/
├── README.md                                # Package guide (this file)
├── pyproject.toml                           # Build metadata and dependencies
├── src/claude_chat_impl/
│   ├── __init__.py                          # Public exports + auto-registration hook
│   ├── auth_manager.py                      # OAuth 2.0 helpers backed by httpx
│   ├── claude_impl.py                       # `ClaudeClient` + factory registration
│   ├── message_impl.py                      # Claude-response translation & message factory
│   └── settings.py                          # Pydantic settings sourced from environment
└── tests/
    ├── conftest.py                          # Shared fixtures for patched SDK calls
    ├── test_auth_manager.py                 # Exercises OAuth URL/token/userinfo helpers
    ├── test_claude_impl.py                  # Validates client behaviour and factory wiring
    └── test_settings.py                     # Ensures settings load from environment safely
```

- `__init__.py` – Exports the key classes and runs `register()` on import so
  `ai_chat_api.get_client` / `get_message` are immediately bound to Claude.
- `claude_impl.py` – Wraps `anthropic.Anthropic` and defines `ClaudeClient`,
  targeting the `claude-3-haiku-20240307` model with sensible defaults.
- `message_impl.py` – Contains `ClaudeMessage` and translation helpers to map
  Anthropic SDK responses into the workspace message abstraction.
- `auth_manager.py` – Drives the OAuth authorization code flow using the
  configured endpoints and credentials.
- `settings.py` – Centralised environment configuration powered by
  `pydantic-settings`. Reads values from `.env` or the process at runtime.

## Environment Configuration
Set the following environment variables (or provide them via a `.env` file) so
`AppSettings` can hydrate correctly:

- `ANTHROPIC_API_KEY` – Claude API key for calling the Anthropic SDK.
- `OAUTH_CLIENT_ID` / `OAUTH_CLIENT_SECRET` – Google OAuth credentials.
- `OAUTH_REDIRECT_URI` – Callback URL registered with the OAuth provider
  (defaults to `http://127.0.0.1:8000/auth/callback`).
- `OAUTH_AUTH_URL`, `OAUTH_TOKEN_URL`, `OAUTH_USERINFO_URL` – Override endpoints
  when targeting a different identity provider (Google defaults are prefilled).
- `SESSION_SECRET_KEY` – Symmetric key used to sign JWT session cookies.
- `SESSION_ALGORITHM` – JWT signing algorithm, defaulting to `HS256`.

These settings are shared with `ai_chat_service`, so configure them before
starting the FastAPI application.

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

The suite patches Anthropic and HTTP interactions to keep runs fast and
deterministic while covering the registration, OAuth, and settings logic.
