# AI Conversation API

## Overview
`ai_conversation_api` defines the abstract interfaces that every AI conversation provider must implement. The package offers only the contract layer and a factory hook—no concrete logic.

## Purpose
- Describe the interaction surface available to consumers of conversational backends.
- Provide a single factory (`get_client`) that concrete adapters can override.
- Keep conversation-specific types explicit through the `ai_conversation_api.message` and `ai_conversation_api.session` modules.

## Architecture

### Component Design
The package exposes an abstract `Client` that is responsible for creating and managing conversation *sessions*. Sessions implement the `Session` contract and in turn produce `Message` objects. No concrete networking or storage logic ships with the API package.

### API Integration
```python
from ai_conversation_api import Client, get_client
from ai_conversation_api.session import Session
from ai_conversation_api.message import Message

client: Client = get_client()
session: Session = client.create_session()
reply: Message = client.send(content="Hello!")
```

### Dependency Injection
Implementation packages (for example `openai_conversation_impl`) replace the factory at import time:
```python
import openai_conversation_impl  # rebinds ai_conversation_api.get_client

from ai_conversation_api import get_client
client = get_client()
```

## API Reference

### Client Abstract Base Class
```python
class Client(ABC):
    ...
```

#### Methods
- `create_session(*, name: str | None = None, **kwargs: Any) -> Session`: Start a new conversational session.
- `send(content: str, *, session_id: str | None = None) -> Message`: Append a user message, creating a session when none supplied.
- `get_session(session_id: str) -> Session`: Retrieve a previously created session.
- `list_sessions() -> Iterable[Session]`: Enumerate known sessions.
- `delete_session(session_id: str) -> bool`: Remove a session if supported by the provider.

### Session Abstract Base Class
```python
class Session(ABC):
    ...
```

#### Key Properties / Methods
- `id -> str`: Stable identifier for the session.
- `model -> str | None`: Optional identifier for the backing model.
- `history -> Iterable[Message]`: Immutable view of past messages.
- `send(content: str) -> Message`: Append a user message and return the assistant reply.
- `reset() -> None`: Clear stored context.

### Message Abstract Base Class
```python
class Message(ABC):
    ...
```

#### Key Properties
- `id -> str`: Unique identifier for the message.
- `role -> str`: Sender role (for example `user`, `assistant`, `system`).
- `content -> str`: Textual payload.

### Factory Function
`get_client(*, api_key: str | None = None, **kwargs: Any) -> Client`: Returns the bound implementation or raises `NotImplementedError` when none registered.

## Usage Examples

### Basic Flow
```python
from ai_conversation_api import get_client

client = get_client()
session = client.create_session()

greeting = session.send("Hello!")
print(greeting)

follow_up = client.send("Remind me to stretch every hour.")
print(follow_up)
```

## Implementation Checklist
1. Implement every abstract method in `Client`, `Session`, and any other relevant contracts.
2. Return objects compatible with `ai_conversation_api.session.Session` and `ai_conversation_api.message.Message`.
3. Publish a factory (for example `get_client_impl`) and assign it to `ai_conversation_api.get_client`.
4. Honour the optional `session_id` parameter in `Client.send` by creating or reusing a sensible default session when omitted.

## Testing
```bash
uv run pytest src/ai_conversation_api/tests/ -q
uv run pytest src/ai_conversation_api/tests/ --cov=src/ai_conversation_api --cov-report=term-missing
```
