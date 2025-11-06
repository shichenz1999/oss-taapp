# AI Chat API

## Overview
`ai_chat_api` captures the minimal interface that every AI chat backend must
implement to plug into the OSS TA application. It standardises the message
shape, exposes a factory hook for dependency injection, and keeps the rest of
the system decoupled from provider-specific SDKs.

## Responsibilities
- Define the `Client` contract that orchestrates single-turn prompt/response flows.
- Describe the `Message` abstraction consumed by downstream services.
- Expose overridable factories (`get_client`, `get_message`) so concrete
  implementations can register themselves at import time.
- Supply a small test suite that guards the public surface and expectations.

## Key Modules
```
ai_chat_api/
├── README.md                                # Package guide (this file)
├── pyproject.toml                           # Build metadata and dependencies
├── src/ai_chat_api/
│   ├── __init__.py                          # Re-exports + factory placeholders
│   ├── client.py                            # `Client` ABC and `get_client` hook
│   └── message.py                           # `Message` ABC and `get_message` hook
└── tests/
    └── test_ai_chat_api.py                  # Contract-focused regression tests
```

- `src/ai_chat_api/__init__.py` – Presents the public API (`Client`, `Message`,
  and factory references) and allows implementations to mutate the factories.
- `src/ai_chat_api/client.py` – Houses the abstract client definition that
  providers subclass before binding `get_client`.
- `src/ai_chat_api/message.py` – Captures the assistant message contract and
  the companion `get_message` factory.
- `src/ai_chat_api/tests/test_ai_chat_api.py` – Exercises basic import and
  contract behaviour so regressions are surfaced quickly.

## Interface Contracts
- **Client.send_message(prompt, user_id)** – Synchronous call that receives a
  human prompt and returns a provider-specific `Message`. Implementations should
  handle retries, tracing, and telemetry before returning.
- **get_client() -> Client** – Factory method swapped at runtime (e.g. by
  `claude_chat_impl.register()`) to deliver the active client instance or
  dependency-injected copy.
- **Message.role / Message.content** – Read-only properties that expose the
  assistant's role label and textual body. Implementations may store additional
  metadata but the interface guarantees these accessors.
- **get_message(role, content) -> Message** – Companion factory that lets other
  layers create message objects without coupling to a concrete class.

## Example Usage
```python
from ai_chat_api import Client

def trigger_prompt(api_client: Client, prompt: str, user_id: str) -> str:
    message = api_client.send_message(prompt=prompt, user_id=user_id)
    return f"{message.role}: {message.content}"
```

Most services import `get_client` so the active implementation can be swapped
for tests:

```python
from ai_chat_api import get_client

chat_client = get_client()
reply = chat_client.send_message(prompt="Summarise the syllabus", user_id="user-123")
```

## Implementing a Provider
1. Subclass `ai_chat_api.Client` and implement `send_message`.
2. Provide a concrete `Message` class that honours `role` and `content`.
3. Expose a module-level `register()` that rebinds `ai_chat_api.get_client` and,
   optionally, `ai_chat_api.get_message`.
4. Ensure the registration hook runs on import so dependent services can simply
   `import your_impl`.

## Testing
```bash
uv run pytest src/ai_chat_api/tests/test_ai_chat_api.py
```

When adding new behaviours, extend the contract tests to keep consumers aligned
on expectations.
