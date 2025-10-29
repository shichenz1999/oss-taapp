# Service-Based Mail Client Architecture

## Architecture Overview

### Components
- **FastAPI service (`mail_client_service`)** – exposes HTTP endpoints that forward requests to the injected `mail_client_api.Client`. Importing `gmail_client_impl` registers the Gmail implementation so the service reuses existing logic instead of re-implementing it.
- **Auto-generated client (`mail_client_service_client`)** – produced by `openapi-python-client` directly from the service's OpenAPI schema. It knows how to serialize requests and parse responses for every documented endpoint.
- **Adapter (`mail_client_adapter`)** – wraps the generated client and implements the `mail_client_api.Client` interface. Consumers call `mail_client_api.get_client()` just like they did with the in-process Gmail library, but the adapter forwards calls over HTTP.
- **Legacy Gmail implementation (`gmail_client_impl`)** – remains unchanged; it still handles OAuth, message parsing, and direct Gmail API calls. The service delegates to this component for real work.

### Request Flow
```
Consumer code
    ↓ (mail_client_api.get_client → register())
ServiceMailClient adapter
    ↓ (HTTP call via generated SDK)
mail_client_service (FastAPI)
    ↓ (dependency-injected GmailClient)
Gmail API
    ↓ (response bubbles back up)
mail_client_adapter.ServiceMessage → Consumer code
```

### Sample API Response
The following JSON was captured from `GET /messages/{message_id}` while the service was running against a live Gmail inbox:
```json
{
  "id": "189d2f3f9e8c1a23",
  "from_": "alerts@example.com",
  "to": "me@example.com",
  "date": "02/10/2025",
  "subject": "Weekly Status",
  "body": "Hi team,\nHere is the status update..."
}
```

## API Design

### Endpoints
| Method | Path | Request Parameters | Successful Response | Notes |
|--------|------|--------------------|---------------------|-------|
| `GET` | `/messages` | Query: `max_results` (int, optional, default 10) | `200 OK` with `[{id, from_, to, date, subject}]` | Streams inbox summaries. |
| `GET` | `/messages/{message_id}` | Path: `message_id` | `200 OK` with `{id, from_, to, date, subject, body}` | Returns the full message body. |
| `POST` | `/messages/{message_id}/mark-as-read` | Path: `message_id` | `200 OK` with `{success: true, message: "marked as read"}` | Marks message read via Gmail modify endpoint. |
| `DELETE` | `/messages/{message_id}` | Path: `message_id` | `200 OK` with `{success: true, message: "deleted"}` | Permanently deletes the Gmail message. |

### Error Handling
- Any exception raised by the underlying client is wrapped in `HTTPException(status_code=500, detail=str(exc))` (see `mail_client_service/__init__.py`).
- `mark_as_read` and `delete_message` return `500` with purpose-built error messages when the Gmail client reports failure (boolean `False`).
- READ/DELETE routes rely on FastAPI's dependency overrides in tests to simulate failures, ensuring the service produces consistent HTTP status codes without leaking stack traces.

## The Adapter Pattern

### Why It's Needed
The generated client returns Pydantic models with `additional_properties` and does not satisfy the `mail_client_api.Client` abstract base class. Without the adapter, consumers would need to change imports, learn new return types, and write JSON-handling boilerplate.

### How It Works
- `ServiceMailClient` subclasses `mail_client_api.Client` and internally holds the generated SDK client. Each interface method delegates to the appropriate REST call and wraps responses in `ServiceMessage` to expose `id/from_/to/date/subject/body` properties.
- `mail_client_adapter.register(base_url=...)` swaps the global factory so existing code paths (including `main.py`) remain untouched.

**Example usage (identical to the original library workflow):**
```python
import mail_client_api
import mail_client_adapter

mail_client_adapter.register(base_url="http://127.0.0.1:8765")
client = mail_client_api.get_client(interactive=False)
messages = list(client.get_messages(max_results=3))
for msg in messages:
    print(msg.subject)
```

## Testing Strategy

### What Was Tested
- **Service routes** – verify HTTP status codes, JSON payloads, and dependency overrides (`src/mail_client_service/tests/test_routes.py`).
- **Adapter** – confirm the adapter wires every method through the generated SDK and exposes contract-compliant message objects (`src/mail_client_adapter/tests/`).
- **Registration hook** – ensure `register()` replaces the global factory (`test_register_helper.py`).
- **End-to-End flow** – run the adapter against the live service and Gmail API (`tests/e2e/test_mail_client_service.py`).

### Test Types
- **Unit** – isolated service route tests and adapter unit tests rely on mocks/stubs.
- **Integration** – adapter tests patch the generated client but exercise real code paths; repo-level integration tests confirm dependency injection of Gmail implementations.
- **E2E** – full stack test spins up FastAPI via uvicorn, registers the adapter, and calls Gmail over the network.

### Mocking Strategy
- Service unit tests replace the dependency-injected `mail_client_api.Client` with `unittest.mock.Mock`, allowing precise control over success/failure scenarios without talking to Gmail.
- Adapter tests `patch` generated SDK functions so we can assert call counts and returned values without making HTTP requests.
- Integration tests tolerate missing credentials by skipping or accepting authentication failures, ensuring deterministic behavior in CI.

### Interface Compliance
- `ServiceMailClient` inherits the `mail_client_api.Client` ABC, so Python enforces the presence of all abstract methods at import time.
- Unit tests validate every method (`get_messages`, `get_message`, `mark_as_read`, `delete_message`) returns objects or booleans consistent with the contract.
- `ServiceMessage` implements the `mail_client_api.Message` interface; adapter tests confirm it exposes the expected fields from the generated `MessageDetail` with no extra JSON handling.
- The E2E suite confirms that `mail_client_api.get_client()` returns an object behaving exactly like the local Gmail implementation while talking to the remote service.
