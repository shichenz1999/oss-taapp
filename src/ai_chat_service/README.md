# AI Chat Service

## Overview
`ai_chat_service` packages the AI chat contract inside a FastAPI
application. It exposes a lightweight HTTP surface with a readiness probe and a
single `/chat` endpoint that forwards prompts (plus optional instructions and
JSON schemas) to the active `ai_chat_api.AIInterface` implementation
(registered by importing `claude_chat_impl`).

## Responsibilities
- Serve the `/health` readiness endpoint for infrastructure checks.
- Accept chat prompts (plus optional system prompt and response schema) and
  return whatever the configured AI interface produces.
- Provide dependency inversion hooks so tests can swap the underlying
  `AIInterface` implementation.

## Key Modules
```
ai_chat_service/
├── README.md                                # Package guide (this file)
├── pyproject.toml                           # Build metadata and dependencies
├── src/ai_chat_service/
│   ├── __init__.py                          # Package marker
│   └── main.py                              # FastAPI application + dependency wiring
└── tests/
    └── test_main.py                         # Integration-style tests for routing + dependency overrides
```

- `src/ai_chat_service/main.py` – Instantiates `FastAPI`, defines the `/health`
  and `/chat` routes, and injects the active AI interface via
  `ai_chat_api.get_ai_interface`.
- `src/ai_chat_service/tests/test_main.py` – Exercises the health probe, chat
  responses with overridden dependencies, and error propagation.

## HTTP Routes
- `GET /health` – Lightweight readiness probe that returns `{"status": "ok"}`.
- `POST /chat` – Accepts a JSON payload with `user_input`, optional
  `system_prompt`, and optional `response_schema`. Returns the AI response as
  either a plain string or a structured JSON object. Example (no schema):
  ```json
  {
    "response": "Here is your summarised response."
  }
  ```
  When a schema is provided, the AI can emit structured outputs such as tool
  invocations. For instance:
  ```json
  {
    "user_input": "Review ticket A-102 and delete it if necessary.",
    "system_prompt": "You are a ticket triage assistant.",
    "response_schema": {
      "type": "object",
      "properties": {
        "text": { "type": "string" },
        "tools": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "args": { "type": "object" }
            },
            "required": ["name", "args"]
          }
        }
      },
      "required": ["text"]
    }
  }
  ```

## Running the Service
```bash
uv run uvicorn ai_chat_service.main:app --reload
curl -X POST http://127.0.0.1:8000/chat \
  -d '{"user_input": "List upcoming assignments"}' \
  -H "Content-Type: application/json"
```

Configure `claude_chat_impl.settings.ANTHROPIC_API_KEY` before launching.

## Testing
```bash
uv run pytest src/ai_chat_service/tests -q
```

Tests override FastAPI dependencies to simulate chat responses and error cases.
