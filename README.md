# OSS TA Application

[![CircleCI](https://circleci.com/gh/ivanearisty/oss-taapp.svg?style=shield)](https://circleci.com/gh/ivanearisty/oss-taapp)
[![Coverage](https://img.shields.io/badge/coverage-85%2B%25-brightgreen)](https://circleci.com/gh/ivanearisty/oss-taapp)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

The repository hosts two homework deliverables that share a common toolchain and workspace layout:

- **HW1 – Component-Based Mail Client**: Builds an abstract mail client contract with a Gmail implementation and adapter/service layers.
- **HW2 – Claude Chat Service**: Extends the project with a Claude-powered chat API, OAuth login flow, and FastAPI deployment unit.

Both assignments follow the same engineering standards: strict interface boundaries, dependency injection, and automated checks via `uv`, Ruff, MyPy, and Pytest.

---

## Repository Structure

```
oss-taapp/
├── docs/                         # MkDocs documentation
├── src/
│   ├── mail_client_api/          # HW1 abstract contract
│   ├── gmail_client_impl/        # HW1 Gmail implementation
│   ├── mail_client_service/      # HW1 FastAPI service for mail
│   ├── mail_client_service_client/ # Generated SDK consumed by the adapter
│   ├── mail_client_adapter/      # HW1 adapter for generated client
│   ├── ai_chat_api/              # HW2 abstract contract
│   ├── claude_chat_impl/         # HW2 Claude + OAuth implementation
│   ├── ai_chat_service/          # HW2 FastAPI deployment
│   ├── ai_chat_service_api_client/ # Generated SDK for the chat service
│   └── ai_chat_adapter/          # HW2 adapter for the generated client
├── tests/                        # Cross-component tests
├── README.md
├── pyproject.toml                # Workspace + tooling config
└── uv.lock                       # Locked dependency graph
```

---

## Shared Development Setup

1. **Install prerequisites**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh   # macOS / Linux
   # or use the PowerShell installer on Windows
   ```
2. **Clone and bootstrap**
   ```bash
   git clone <repo-url>
   cd oss-taapp
   uv sync --all-packages --extra dev
   ```
3. **Activate the virtual environment (optional)**
   ```bash
   source .venv/bin/activate  # macOS / Linux
   .venv\Scripts\Activate.ps1 # Windows PowerShell
   ```

The `uv sync` step installs every workspace package (HW1 and HW2) plus development tooling such as Ruff, MyPy, Pytest, and Pytest-Mock.

Useful commands from the repo root:

```bash
uv run ruff check .            # Lint
uv run ruff format --check .   # Formatting check
uv run mypy src tests          # Static typing
uv run pytest -q               # Full test suite (coverage enforced)
uv run mkdocs serve            # Live docs at http://127.0.0.1:8000
```

---

## HW1 – Mail Client Platform

### Goal
Establish a reusable email client architecture with clean abstractions and a Gmail-backed implementation. Core packages:

- `mail_client_api`: Abstract `Client` + `Message` contracts and factory hook.
- `gmail_client_impl`: Production Gmail client implementing the contract.
- `mail_client_adapter`: HTTP adapter that wraps the generated SDK.
- `mail_client_service`: FastAPI service exposing mailbox operations.

### Required Credentials

| Variable / File        | Purpose                                    |
|------------------------|--------------------------------------------|
| `.env`                 | Optional helper to store Gmail variables   |
| `credentials.json`     | OAuth client secrets from Google Cloud     |
| `token.json`           | Generated after the initial OAuth flow     |
| `GMAIL_CLIENT_ID`      | Alternative to `credentials.json`          |
| `GMAIL_CLIENT_SECRET`  | Alternative to `credentials.json`          |
| `GMAIL_REFRESH_TOKEN`  | Refresh token for service accounts/CI      |

### Running the Demonstration Script

```bash
uv run python main.py
```

This launches the legacy CLI demo that fetches recent messages via the Gmail API. The first run performs OAuth consent and creates `token.json`.

### Service + Adapter Flow

1. Start the service:
   ```bash
   uv run python -m mail_client_service.main
   ```
2. Use the adapter in client code:
   ```python
   import mail_client_api
   import mail_client_adapter

   mail_client_adapter.register(base_url="http://127.0.0.1:8765")
   client = mail_client_api.get_client(interactive=False)
   print(next(client.get_messages()).subject)
   ```

### Testing

```bash
uv run pytest src/mail_client_api/tests -q
uv run pytest src/gmail_client_impl/tests -q
uv run pytest tests/integration -q        # Optional, requires credentials
uv run pytest tests/e2e -m "not local_credentials"
```

Pytest markers such as `integration`, `e2e`, and `local_credentials` let you target the right portions of the suite.

---

## HW2 – Claude Chat Service

### Goal
Deliver a minimal Claude-powered chat microservice with OAuth-protected access. Core packages:

- `ai_chat_api`: Abstract interface + dataclass message model.
- `claude_chat_impl`: Concrete Anthropic client that registers itself with the API contract.
- `ai_chat_service`: FastAPI deployment exposing `/auth/*` and `/chat`, plus the OAuth helpers.
- `ai_chat_adapter`: HTTP adapter that uses the generated `ai_chat_service_api_client` package so callers stay on the abstract contract.

### Environment Variables

Place the following in `.env` (the settings loader walks parent directories to find it):

```env
ANTHROPIC_API_KEY=sk-ant-...                               # used by claude_chat_impl
OAUTH_CLIENT_ID=your-google-client-id                      # used by ai_chat_service
OAUTH_CLIENT_SECRET=your-google-client-secret              # used by ai_chat_service
SESSION_SECRET_KEY=long-random-string                      # used by ai_chat_service
OAUTH_TOKEN_URL=https://oauth2.googleapis.com/token        # optional override for ai_chat_service
OAUTH_REDIRECT_URI=http://127.0.0.1:8000/auth/callback     # must match Google config (ai_chat_service)
```

> **Tip:** Google’s redirect URIs must be registered in the Cloud Console. The service expects to run locally on port `8000`.

### Running the Service

```bash
uvicorn ai_chat_service.main:app --reload
uv run uvicorn smart_chat_bot.main:app --reload
```

Available routes:

- `GET /` → redirects to the interactive Swagger UI
- `GET /health` → simple 200 OK
- `GET /auth/login` → redirects to Google OAuth consent screen
- `GET /auth/logout` → clears the session cookie and redirects back to `/docs`
- `GET /auth/callback` → exchanges the `code`, sets a `session_token` cookie, and redirects to `/docs`
- `POST /chat` → requires the session cookie, forwards the prompt to Claude, returns an assistant `Message`

The implementation is stateless; each request sends a single prompt with no history. Errors from Anthropic or the OAuth flow surface as HTTP 500 responses with concise messages.

### Testing

```bash
uv run pytest src/ai_chat_api/tests -q
uv run pytest src/claude_chat_impl/tests -q
uv run pytest src/ai_chat_service/tests -q
uv run pytest src/ai_chat_adapter/tests -q
```

The suite covers the abstract contract, OAuth flow (now hosted in `ai_chat_service`), JWT/session helpers, message translation, and FastAPI routes. Coverage is enforced at 85%.

---

## Continuous Integration & Docs

- CircleCI pipeline (`.circleci/config.yml`) runs Ruff, MyPy, unit tests, and CI-safe subsets of the suite. Secrets are injected via environment variables during the build.
- Documentation lives in `docs/` and is published with MkDocs Material. Use `uv run mkdocs serve` for live previews.

For deeper explanations of each component and the testing philosophy, see:

- `docs/index.md` – high-level design goals
- `docs/component.md` – in-depth component architecture
- `docs/testing.md` – how we structure tests and use markers
- `docs/gmail_refresh_token.md` – guidance on managing Gmail refresh tokens
- `DESIGN.md` – background on the service-based mail client architecture

---

## FAQ

- **Why do settings fail even though `.env` exists?**  
  `AppSettings` walks parent directories when locating `.env`. Ensure the file is at the repo root or export the variables in your shell.

- **OAuth callback returns 500.**  
  Confirm that `OAUTH_TOKEN_URL` is `https://oauth2.googleapis.com/token` and that the redirect URI configured in Google Cloud matches `OAUTH_REDIRECT_URI`.

- **Where do coverage requirements come from?**  
  `pyproject.toml` enforces an 85% minimum across the workspace. If you add modules, include tests or mark them with `pragma: no cover` where appropriate.

---

Happy hacking! Each homework builds on the same tooling, so once the workspace is synced you can switch between HW1 and HW2 without reconfiguring your environment. Keep credentials secure, reuse the provided test markers, and lean on the docs to understand each component’s responsibilities.

## Deployment

The AI chat service runs on Render at **https://oss-taapp-aen3.onrender.com**.

**How to use**

1. Visit `https://oss-taapp-aen3.onrender.com/auth/login` and sign in with Google. After authentication you will be redirected back to Swagger UI.
2. Execute the `/chat` operation from Swagger UI (or any HTTP client) to converse with Claude.

**Interfaces**

- `/docs`: interactive Swagger UI
- `/health`: health check
- `/auth/login`: Google authentication and login
- `/auth/logout`: logout
- `/auth/callback`: authentication callback
- `/chat`: chat interface
- `/openapi.json`: base URL that `openapi-python-client` can consume
