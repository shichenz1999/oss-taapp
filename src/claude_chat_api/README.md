# Claude Chat API

## Overview
`claude_chat_api` defines the abstract contract for integrating a Claude-powered chat
service into the OSS TA application. The package provides the minimal message model and
interface needed to validate the system architecture before wiring real network calls.

## Purpose
- Document the single-message interaction the platform expects from any Claude adapter.
- Share strongly-typed message models with the rest of the workspace.
- Allow dynamic injection of concrete implementations that satisfy the abstract API.

## Architecture

### Component Design
The package exposes:
- `MessageRole`: Enum describing whether a message originated from the user or the assistant.
- `Message`: Pydantic model capturing the role and textual content of a chat exchange.
- `AbstractClaudeChatAPI`: Abstract base class defining the `send_message` entry point.

### Interaction Pattern
```python
from claude_chat_api import AbstractClaudeChatAPI, Message, MessageRole

def trigger_prompt(api: AbstractClaudeChatAPI, prompt: str, *, user_id: str) -> Message:
    return api.send_message(prompt=prompt, user_id=user_id)
```

## Implementation Checklist
1. Subclass `AbstractClaudeChatAPI` and implement `send_message`.
2. Return a `Message` instance with `role=MessageRole.ASSISTANT`.
3. Ensure authentication/authorization happens prior to calling `send_message`.
4. Decide how to persist or replay conversation state if multi-turn interactions are required.

## Testing
```bash
uv run pytest src/claude_chat_api/tests/ -q
uv run pytest src/claude_chat_api/tests/ --cov=src/claude_chat_api --cov-report=term-missing
```
