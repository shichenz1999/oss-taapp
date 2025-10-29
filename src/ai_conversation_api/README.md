# AI Conversation API

## Overview
`ai_conversation_api` defines the abstract interfaces that every AI conversation provider must implement. The package offers only the contract layer and a factory hook—no concrete logic.

## Purpose
- Describe the interaction surface available to consumers of conversational backends.
- Provide a single factory (`get_client`) that concrete adapters can override.
- Keep conversation-specific types explicit through the `ai_conversation_api.message` module.

## Architecture

### Component Design
The package exposes one abstract client focused on conversational flows—creating threads, sending messages, retrieving history, and streaming replies. It depends solely on the `Message` and `Conversation` abstractions.

### API Integration
```python
from ai_conversation_api import Client, get_client
from ai_conversation_api.message import Conversation, Message

client: Client = get_client()
conversation: Conversation = client.create_conversation()
reply: Message = client.send_message(conversation_id=conversation.id, content="Hello!")
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
- `create_conversation() -> Conversation`: Start a new conversation thread.
- `send_message(content: str, *, conversation_id: str | None = None, stream: bool = False) -> Message | Iterator[Message]`: Append a user message, optionally stream the assistant reply, and create a default conversation when none supplied.
- `get_conversation(conversation_id: str) -> Conversation`: Retrieve a conversation with its accumulated messages.
- `list_messages(conversation_id: str, *, max_results: int | None = None) -> Iterator[Message]`: Iterate over messages in a conversation.
- `list_conversations(max_results: int = 10) -> Iterator[Conversation]`: Enumerate conversations.
- `delete_conversation(conversation_id: str) -> bool`: Remove a conversation if supported by the provider.

### Factory Function
`get_client(*, api_key: str | None = None, **kwargs: Any) -> Client`: Returns the bound implementation or raises `NotImplementedError` when none registered.

## Usage Examples

### Basic Flow
```python
from ai_conversation_api import get_client

client = get_client()
conversation = client.create_conversation()

greeting = client.send_message(conversation_id=conversation.id, content="Hello!")
print(greeting.content)
```

### Streaming Replies
```python
from ai_conversation_api import get_client

client = get_client()
conversation = client.create_conversation()

for chunk in client.send_message(
    conversation_id=conversation.id,
    content="Please explain quicksort step by step.",
    stream=True,
):
    print(chunk.content, end="", flush=True)
```

## Implementation Checklist
1. Implement each abstract method in `Client`.
2. Return objects compatible with `ai_conversation_api.message.Message` and `Conversation`.
3. Publish a factory (for example `get_client_impl`) and assign it to `ai_conversation_api.get_client`.
4. Honour the optional `conversation_id` parameter in `send_message` by creating or reusing a sensible default thread when omitted.

## Testing
```bash
uv run pytest src/ai_conversation_api/tests/ -q
uv run pytest src/ai_conversation_api/tests/ --cov=src/ai_conversation_api --cov-report=term-missing
```
