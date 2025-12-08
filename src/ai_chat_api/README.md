# AI Chat API

## Overview
`ai_chat_api` captures the minimal interface that every AI chat backend must
implement to plug into the OSS TA application. It standardises the structured
response shape, exposes a factory hook for dependency injection, and keeps the
rest of the system decoupled from provider-specific SDKs.

## Responsibilities
- Define the `AIInterface` contract that orchestrates prompt/response flows.
- Provide the `AIStructuredResponse` model for JSON-shaped outputs (with
  strict intents and a user-facing message).
- Expose an overridable factory (`get_ai_interface`) so concrete implementations
  can register themselves at import time.
- Supply a small test suite that guards the public surface and expectations.

## Key Modules
```
ai_chat_api/
├── README.md                                # Package guide (this file)
├── pyproject.toml                           # Build metadata and dependencies
├── src/ai_chat_api/
│   ├── __init__.py                          # Re-exports + factory placeholder
│   └── ai_chat_api.py                       # `AIInterface` ABC and response model
└── tests/
    └── test_ai_chat_api.py                  # Contract-focused regression tests
```

- `src/ai_chat_api/__init__.py` – Presents the public API (`AIInterface`,
  `AIStructuredResponse`, and factory reference) and allows implementations to
  mutate the factory.
- `src/ai_chat_api/ai_chat_api.py` – Houses the abstract interface definition
  and structured response model.
- `src/ai_chat_api/tests/test_ai_chat_api.py` – Exercises basic import and
  contract behaviour so regressions are surfaced quickly.

## Interface Contracts
- **AIInterface.generate_response(user_input, system_prompt, response_schema=None)**
  – Synchronous call that receives a human prompt and returns either free text
  (string) or an `AIStructuredResponse` when structured output is requested.
- **AIStructuredResponse** – Pydantic model with `intent: Literal[...]`,
  `message: str`, and `parameters: dict[str, Any]` for JSON action payloads.
- **get_ai_interface() -> AIInterface** – Factory method swapped at runtime
  (e.g. by `claude_chat_impl.register()`) to deliver the active implementation
  or dependency-injected copy.

## Example Usage
```python
from ai_chat_api import AIInterface, get_ai_interface, AIStructuredResponse

def trigger_prompt(api_client: AIInterface, prompt: str) -> str:
    reply = api_client.generate_response(
        user_input=prompt,
        system_prompt="You are a helpful assistant.",
    )
    if isinstance(reply, AIStructuredResponse):
        return f"{reply.intent}: {reply.parameters}"
    return reply

chat_client = get_ai_interface()
print(trigger_prompt(chat_client, "Summarise the syllabus"))
```

## Implementing a Provider
1. Subclass `ai_chat_api.AIInterface` and implement `generate_response`.
2. Return strings for conversational responses or `AIStructuredResponse` for
   structured JSON outputs.
3. Expose a module-level `register()` that rebinds `ai_chat_api.get_ai_interface`.
4. Ensure the registration hook runs on import so dependent services can simply
   `import your_impl`.

## Testing
```bash
uv run pytest src/ai_chat_api/tests/test_ai_chat_api.py
```

When adding new behaviours, extend the contract tests to keep consumers aligned
on expectations.
