# Claude Chat Client (OpenAPI-generated SDK + Adapter)

This guide shows how to generate a type-safe HTTP client from the `claude_chat_service` OpenAPI spec using `openapi-python-client`, and how to wrap it with an adapter that implements the original `AbstractClaudeChatAPI` so callers don't need to deal with HTTP details.

## Overview

- Auto-generated client: Create a lightweight, type-safe SDK from the service's OpenAPI spec (similar to `src/mail_client_service_client`).
- Service client adapter: In `claude_chat_adapter`, provide `ServiceClaudeChat` implementing `AbstractClaudeChatAPI` and delegating to the generated SDK.

## Step 1: Export the service OpenAPI spec

We provide `scripts/export_claude_openapi.py`. Running it writes `docs/claude_chat_service_openapi.json`.

```powershell
# Recommended: use uv (dev dependencies are already configured)
uv run python -m scripts.export_claude_openapi
```

If you don't use uv, set up a Python venv and install FastAPI + workspace packages (see the root `pyproject.toml`).

## Step 2: Generate the typed client

Use `openapi-python-client` to generate the client package at `src/claude_chat_service_client`:

```powershell
uv run openapi-python-client generate `
  --path .\docs\claude_chat_service_openapi.json `
  --output-path .\src\claude_chat_service_client `
  --overwrite
```

The generated structure looks like:

```
src/claude_chat_service_client/
  claude_chat_service_client/
    api/
      chat/
        send_chat_message_chat_post.py
    client.py
    models/
    types.py
    ...
  pyproject.toml
```

## Step 3: Use the service client adapter

We added `src/claude_chat_adapter` with the core class:

- `claude_chat_adapter.ServiceClaudeChat`: implements `claude_chat_api.AbstractClaudeChatAPI`.
- Constructor parameters:
  - `base_url`: service address (e.g., `http://localhost:8000`)
  - `session_token`: JWT cookie obtained after the service OAuth flow. The adapter sets it as a cookie for authenticated calls.

Example:

```python
from claude_chat_adapter import ServiceClaudeChat

client = ServiceClaudeChat(base_url="http://localhost:8000", session_token="<jwt>")
reply = client.send_message(prompt="Hello", user_id="user@example.com")
print(reply.content)
```

Note: `user_id` is part of the abstract contract; the service identifies the user via the session cookie, so this parameter is not sent over the wire.

## Testing

- Minimal unit tests are included at `src/claude_chat_adapter/tests/test_adapter.py` (they use a dummy client; no live service needed).
- The generated client code is excluded from coverage (see the root `pyproject.toml`).

## Common pitfalls

- “Generated client not found”: run Step 2 to generate the SDK first; tests use a dummy client as a fallback.
- 401 Unauthorized: ensure you completed `/auth/login` -> `/auth/callback` and pass the resulting `session_token` to the adapter.

## References

- Mail service example: `src/mail_client_service_client` (auto-generated) + `src/mail_client_adapter` (adapter).
- Original interface: `src/claude_chat_api/src/claude_chat_api/api.py` and models in `models.py`.