# AI Chat Service

## Overview
`ai_chat_service` packages the AI chat contract inside a FastAPI
application. It authenticates users through OAuth, issues session cookies,
and proxies chat prompts to the active `ai_chat_api.Client`
implementation (currently registered by importing `claude_chat_impl`).

## Responsibilities
- Serve an OAuth-backed HTTP surface for the chat experience.
- Manage the session lifecycle by minting and validating JWT cookies.
- Convert HTTP payloads into `ai_chat_api` messages and expose the result as JSON.
- Provide health and documentation endpoints for infrastructure and operators.
- Offer dependency inversion hooks so tests can swap out authentication or chat clients.

## Key Modules
```
ai_chat_service/
├── README.md                                # Package guide (this file)
├── pyproject.toml                           # Build metadata and dependencies
├── src/ai_chat_service/
│   ├── __init__.py                          # Package marker
│   ├── auth_deps.py                         # Session token helpers + FastAPI dependency
│   └── main.py                              # FastAPI application, routes, and dependency wiring
└── tests/
    └── test_main.py                         # Integration-style tests for auth and chat flows
```

- `src/ai_chat_service/auth_deps.py` – Handles JWT creation and validation by
  reading secrets from `claude_chat_impl.settings`. Exposed as FastAPI
  dependencies (`get_current_user_id`, `create_session_token`).
- `src/ai_chat_service/main.py` – Instantiates `FastAPI`, wires the OAuth
  `AuthManager`, defines each route, and injects the active chat client using
  `ai_chat_api.get_client`.
- `src/ai_chat_service/tests/test_main.py` – Exercises the health probe,
  OAuth redirect/callback behaviour, authentication requirements, and chat
  responses with overridden dependencies.

## HTTP Routes
- `GET /` – Permanently redirects to `/docs` for quick access to the Swagger UI.
- `GET /health` – Lightweight readiness probe that returns `{"status": "ok"}`.
- `GET /auth/login` – Redirects the browser to the external OAuth provider
  (uses `AuthManager.get_authorization_url()`).
- `GET /auth/callback?code=...` – Exchanges the authorization code for tokens,
  fetches the user profile, mints a signed `session_token` cookie, then redirects
  back to `/docs`. Errors raise `400`/`500` with descriptive messages.
- `POST /chat` – Requires the `session_token` cookie. Accepts
  `{"prompt": "<user text>"}` and returns the assistant message the registered
  `ai_chat_api.Client` produced:
  ```json
  {
    "role": "assistant",
    "content": "Here is your summarised response."
  }
  ```

## Authentication Flow
1. `/auth/login` redirects the user to Google's OAuth consent screen using
   client settings from `claude_chat_impl.settings`.
2. `/auth/callback` exchanges the returned `code` for tokens, fetches the
   user email, then issues a signed JWT session cookie
   (`SESSION_SECRET_KEY` + `SESSION_ALGORITHM`).
3. Subsequent requests rely on the `get_current_user_id` dependency to validate
   the cookie and surface the authenticated email address to route handlers.

## Running the Service
```bash
uv run uvicorn ai_chat_service.main:app --reload
curl -H "Cookie: session_token=<token>" \
  -X POST http://127.0.0.1:8000/chat \
  -d '{"prompt": "List upcoming assignments"}' \
  -H "Content-Type: application/json"
```

Ensure the required environment variables for `claude_chat_impl.settings`
(`ANTHROPIC_API_KEY`, OAuth client credentials, and session signing secrets)
are available before launching the service.

## Testing
```bash
uv run pytest src/ai_chat_service/tests/test_main.py
```

Tests override FastAPI dependencies to simulate OAuth flows and chat responses,
so they remain deterministic and offline-friendly.
