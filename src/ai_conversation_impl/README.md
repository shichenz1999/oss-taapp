# AI Conversation Implementation (Claude)

## Overview
`ai_conversation_impl` provides a concrete implementation of the `ai_conversation_api.Client` contract backed by Anthropic’s Claude API. It manages session lifecycle, persists conversation history locally via TinyDB, and returns message objects that satisfy the core API abstractions.

## Purpose

This package acts as the drop-in Claude adapter for the conversation platform:

- **Claude API Integration** – Wraps Anthropic’s Messages API for text completions.
- **Session Management** – Implements `Session` objects that track history and send replies.
- **Local Persistence** – Stores sessions and message history in `claude_sessions.json` using TinyDB.
- **Dependency Injection** – Rebinds `ai_conversation_api.get_client` on import for seamless usage.

## Architecture

### Components
- `ClaudeClient` – Concrete `Client` that creates, retrieves, lists, and deletes sessions.
- `ClaudeSession` – Implements `Session.send`, `Session.history`, and clears messages as needed.
- `ClaudeMessage` – Lightweight `Message` implementation with `id`, `role`, and `content`.
- `TinySessionStore` – Persistence layer for session metadata and conversation records.

### Authentication
- Relies on an Anthropic API key.
- The client looks for `api_key` passed to `get_client(api_key=...)`.
- If omitted, it resolves the key from the `ANTHROPIC_API_KEY` environment variable (with optional support for `.env` when `python-dotenv` is installed).
- Missing keys raise a runtime error early to avoid silent failures.

### Dependency Injection
```python
import ai_conversation_impl  # registers Claude client

from ai_conversation_api import get_client
client = get_client()  # returns ClaudeClient instance
```

## API Reference

### ClaudeClient
Implements all methods from `ai_conversation_api.client.Client`.

Key methods:
- `create_session()` – Generates a new session with a UUID.
- `get_session(session_id)` – Returns a `ClaudeSession` with persisted history.
- `list_sessions()` – Iterates over known sessions from TinyDB.
- `delete_session(session_id)` – Removes the session and its stored messages.
- `send(content, session_id=None)` – Convenience wrapper that proxies to a session.

### ClaudeSession
- `send(content)` – Appends a user message, calls Claude, persists the assistant reply, and returns it.
- `history` – Read-only view of prior messages as `ClaudeMessage` objects.
- `reset()` – Clears stored conversation history for the session.

### Storage
`TinySessionStore` uses `claude_sessions.json` (configurable via constructor) with two tables:
- `sessions` – Tracks session IDs.
- `messages` – Records message metadata (`session_id`, `message_id`, `role`, `content`) ordered by insertion.

## Usage Examples

### Quick Start
```python
import os
import ai_conversation_impl  # noqa: F401
from ai_conversation_api import get_client

os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."
client = get_client()

session = client.create_session()
reply = session.send("Reply in one short sentence: What is the capital of France?")
print(reply)
```

### Reusing Sessions
```python
import ai_conversation_impl
from ai_conversation_api import get_client

client = get_client()
session = client.create_session()

session.send("Summarise: The Eiffel Tower is in Paris.")
session.send("Explain why the tower is iconic in one sentence.")

for message in session.history:
    print(f"{message.role}: {message.content}")
```

### Client-Level Convenience
```python
import ai_conversation_impl
from ai_conversation_api import get_client

client = get_client()
response = client.send("Reply with one sentence: Name a programming language that runs on the JVM.")
print(response)
```

## Authentication Setup

1. **Get an Anthropic API Key** – Create an account and generate a key in the Anthropic console.
2. **Set Environment Variable**:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```
   or use a `.env` file when `python-dotenv` is available.
3. **Optional Direct Parameter**:
   ```python
   from ai_conversation_api import get_client
   client = get_client(api_key="sk-ant-...")
   ```

## Storage Notes
- Default storage location is `claude_sessions.json` in the working directory.
- Delete the file to clear all sessions, or call `client.delete_session(session_id)` for targeted cleanup.
- TinyDB is lightweight JSON storage; no external database is required for local development.

## Testing
```bash
uv run pytest src/ai_conversation_impl/tests/ -q
uv run pytest src/ai_conversation_impl/tests/ --cov=src/ai_conversation_impl --cov-report=term-missing
```
- Unit tests mock Anthropic client calls; no external requests.
- Integration or e2e tests can supply a real API key via environment variables when needed.

## Scripts
- `scripts/ai_conv_example.py` – Comprehensive demo covering session creation, client sends, history listing, and cleanup.
- `scripts/ai_conversation_quickstart.py` – Minimal example that creates a session and sends a single prompt for fast sanity checks.

## Requirements
- Python 3.11+
- `anthropic` Python SDK (see `pyproject.toml`)
- `tinydb` for local persistence
- `python-dotenv` optional (for `.env` loading)

Configure dependencies via:
```bash
uv pip install -e src/ai_conversation_api -e src/ai_conversation_impl
```
