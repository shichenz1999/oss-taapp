# Smart Chat Bot

## Overview
`smart_chat_bot` runs a FastAPI service that polls chat channels (currently
Discord), sends user messages to the configured AI interface, executes ticket
operations, and posts the result back to the channel. It also exposes a small
status endpoint and Prometheus metrics for observability.

## Responsibilities
- Poll configured channels, skipping bot or empty messages.
- Use the active `ai_chat_api.AIInterface` (registered by `claude_chat_impl`) to
  turn messages into structured ticket intents.
- Execute ticket actions via `ticket_api` (backed by `ticket_impl`) and return
  results to chat.
- Provide a heartbeat endpoint and metrics for service monitoring.

## Key Modules
```
smart_chat_bot/
├── README.md
├── pyproject.toml
├── src/smart_chat_bot/
│   ├── __init__.py                          # Package marker
│   ├── main.py                              # FastAPI app + polling loop + dispatch
│   ├── prompts.py                           # System prompt for structured AI output
│   └── schemas.py                           # Pydantic models for AI actions
└── tests/
    ├── test_main.py                         # Unit tests for parsing + intent handling
    ├── test_integration_flow.py             # Stubbed chat + mocked Jira integration flow
    └── test_e2e_flow.py                      # Optional e2e test with real services
```

## Environment Configuration
The service loads environment variables (a `.env` file at the repo root works
well).

Chat + polling:
- `CHAT_PROVIDER` – Chat provider key; only `discord` is supported. Default: `discord`.
- `CHAT_CHANNEL_IDS` – Comma-separated channel IDs to poll. Required.
- `POLL_INTERVAL_SECONDS` – Polling interval in seconds. Default: `8`.
- `MAX_MESSAGES_PER_POLL` – Max messages fetched per channel per poll. Default: `1`.

Discord:
- `DISCORD_BOT_TOKEN` – Bot token used to read/write messages.
- `DISCORD_TOKEN_TYPE` – Authorization token type. Default: `Bot`.

AI:
- `ANTHROPIC_API_KEY` – Required by `claude_chat_impl` to access Claude.

Ticketing:
- `TICKET_USER_ID` – Reporter/user id for ticket operations. Default: `bot-user`.
- `TICKET_PROJECT_KEY` – Jira project key. Default: `TEST`.
- `JIRA_API_BASE` or `JIRA_CLOUD_ID` – Jira API base or cloud id.
- `JIRA_API_TOKEN` – Jira API token.
- `JIRA_API_EMAIL` – Jira account email.

## HTTP Routes
- `GET /` – Returns basic status information and the poll configuration.
- `GET /metrics` – Prometheus metrics exposed by `prometheus-fastapi-instrumentator`.

## Running the Service
```bash
uv sync --all-packages --extra dev
uv run uvicorn smart_chat_bot.main:app --reload
```

The polling loop starts automatically on startup. Make sure your bot has
permission to read message content in the target channels.

## Testing
```bash
uv run pytest src/smart_chat_bot/tests -q
```

The end-to-end test (`test_e2e_flow.py`) requires real credentials; if you want
to skip it:
```bash
uv run pytest src/smart_chat_bot/tests -q -m "not e2e"
```
