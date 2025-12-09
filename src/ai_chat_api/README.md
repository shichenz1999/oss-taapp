# AI Chat API

## Overview
`ai_chat_api` defines the minimal contract that every AI provider must implement
to plug into the OSS TA application. It exposes a single abstract interface,
plus a factory hook that concrete backends override at import time.

## Responsibilities
- Define the `AIInterface` abstraction that supports both conversational replies
  and structured JSON responses.
- Provide the `get_ai_interface()` factory placeholder that concrete packages
  (e.g., `claude_chat_impl`) overwrite during registration.
- Supply a regression test suite that guards the public interface.

## Key Modules
```
ai_chat_api/
├── README.md                                # Package guide (this file)
├── pyproject.toml                           # Build metadata and dependencies
├── src/ai_chat_api/
│   ├── __init__.py                          # Re-exports + factory placeholder
│   └── client.py                            # AIInterface ABC and factory
└── tests/
    └── test_ai_chat_api.py                  # Contract-focused regression tests
```

- `src/ai_chat_api/__init__.py` – Presents the public API (`AIInterface` and
  `get_ai_interface`) so consumers stay decoupled from concrete providers.
- `src/ai_chat_api/client.py` – Houses the abstract definition of
  `AIInterface.generate_response` and the default factory implementation, which
  raises until an implementation registers itself.
- `src/ai_chat_api/tests/test_ai_chat_api.py` – Exercises the contract so API
  changes surface through failing tests.

## Interface Contract
- **AIInterface.generate_response(user_input, system_prompt=None, response_schema=None)** – Returns either a
  conversational `str` or a structured `dict[str, Any]` when a JSON schema is
  provided.
- **get_ai_interface() -> AIInterface** – Factory placeholder that concrete
  implementations replace (e.g., via `claude_chat_impl.register()`).

## Example Usage
```python
from ai_chat_api import get_ai_interface

ai = get_ai_interface()
reply = ai.generate_response(user_input="Summarise the syllabus")
print(reply)
```

Request a structured response by supplying a schema:

```python
schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "next_action": {"type": "string"},
    },
}

ai = get_ai_interface()
structured = ai.generate_response(
    user_input="Plan tomorrow's tasks",
    system_prompt="Project planner",
    response_schema=schema,
)
print(structured["summary"])
```

## Implementing a Provider
1. Subclass `ai_chat_api.AIInterface` and implement `generate_response`.
2. Expose a factory (e.g., `get_ai_interface_impl`) that returns your concrete
   implementation.
3. Provide a module-level `register()` that rebinds `ai_chat_api.get_ai_interface`
   to your factory.
4. Ensure registration runs on import so dependent services can simply
   `import your_impl`.

## Testing
```bash
uv run pytest src/ai_chat_api/tests/test_ai_chat_api.py
```

Extend the contract tests whenever the public interface grows to keep consumers
aligned on expectations.
