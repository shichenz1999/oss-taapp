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
│   ├── auth_manager.py                      # OAuth 2.0 helper for redirects, token exchange, userinfo
│   ├── auth_deps.py                         # Session token helpers + FastAPI dependency
│   ├── settings.py                          # Service-specific configuration (OAuth + session secrets)
│   └── main.py                              # FastAPI application, routes, and dependency wiring
└── tests/
    ├── test_auth_manager.py                 # Unit tests for OAuth helper logic
    └── test_main.py                         # Integration-style tests for auth and chat flows
```

- `src/ai_chat_service/auth_manager.py` – Wraps the OAuth authorization code flow
  (authorization URL, token exchange, and user profile lookup) using `httpx`.
- `src/ai_chat_service/auth_deps.py` – Handles JWT creation and validation by
  reading secrets from `ai_chat_service.settings`. Exposed as FastAPI
  dependencies (`get_current_user_id`, `create_session_token`).
- `src/ai_chat_service/settings.py` – Loads OAuth client credentials and session
  signing configuration from environment variables.
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
- `GET /auth/logout` – Clears the `session_token` cookie and redirects back to `/docs`.
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
   client settings from `ai_chat_service.settings`.
2. `/auth/callback` exchanges the returned `code` for tokens, fetches the
   user email, then issues a signed JWT session cookie
   (`SESSION_SECRET_KEY` + `SESSION_ALGORITHM`).
3. Subsequent requests rely on the `get_current_user_id` dependency to validate
   the cookie and surface the authenticated email address to route handlers.
4. `/auth/logout` deletes the session cookie and redirects users back to the docs UI.

## Running the Service
```bash
uv run uvicorn ai_chat_service.main:app --reload
curl -H "Cookie: session_token=<token>" \
  -X POST http://127.0.0.1:8000/chat \
  -d '{"prompt": "List upcoming assignments"}' \
  -H "Content-Type: application/json"
```

Configure the following environment variables before launching:
- `ai_chat_service.settings`: `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`,
  `SESSION_SECRET_KEY`, and optional overrides (`OAUTH_REDIRECT_URI`, etc.).
- `claude_chat_impl.settings`: `ANTHROPIC_API_KEY` (required by the Claude client).

## Testing
```bash
uv run pytest src/ai_chat_service/tests/test_main.py
```

Tests override FastAPI dependencies to simulate OAuth flows and chat responses,
so they remain deterministic and offline-friendly.
