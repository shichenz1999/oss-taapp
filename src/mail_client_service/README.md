# Mail Client Service

## Overview
`mail_client_service` wraps a FastAPI application around the `mail_client_api.Client` contract so mailbox capabilities are reachable over HTTP. On import it loads `gmail_client_impl` to register the Gmail-backed client by default, but any package can swap the dependency by rebinding `mail_client_api.get_client` before startup.

## Responsibilities
- Serve HTTP routes for core mailbox actions (list, fetch, mark-as-read, delete).
- Serialise `mail_client_api.Message` instances into consistent JSON payloads.
- Provide a dependency hook (`get_mail_client`) so tests or alternative adapters can swap the client implementation.

## Key Modules
```
mail_client_service/
├── README.md                                # Package guide (this file)
├── pyproject.toml                           # Package metadata and dependency definitions
├── src/mail_client_service/
│   ├── __init__.py                          # FastAPI app + dependency shims for consumers
│   ├── main.py                              # Route handlers, dependency wiring, client cache helpers
│   └── models.py                            # Pydantic response schemas shared by the API
└── tests/
    └── test_routes.py                       # Unit tests for the HTTP layer using fake mail clients
```

- `src/mail_client_service/src/mail_client_service/__init__.py` – Re-exports `app`, `get_mail_client`, and `reset_client_cache` so the package can be mounted with a single import.
- `src/mail_client_service/src/mail_client_service/main.py` – Builds the FastAPI instance, defines each route, and manages the cached `mail_client_api.Client`.
- `src/mail_client_service/src/mail_client_service/models.py` – Declares the Pydantic models serialised in API responses (`MessageSummary`, `MessageDetail`, `OperationResponse`).
- `src/mail_client_service/tests/test_routes.py` – Exercises success and failure flows by overriding `get_mail_client` with mocks.

## API Reference

### `GET /messages`
Returns message summaries.
- **Query parameters**: `max_results` (int, default `10`).
- **200 response**:
  ```json
  [
    {
      "id": "msg-1",
      "from_": "sender@example.com",
      "to": "recipient@example.com",
      "date": "2025-10-03",
      "subject": "Subject line"
    }
  ]
  ```
- **500 response**: `{"detail": "<client error message>"}` if the underlying client raises.

### `GET /messages/{message_id}`
Returns a full message (summary fields plus `body`).
- **200 response**:
  ```json
  {
    "id": "msg-1",
    "from_": "sender@example.com",
    "to": "recipient@example.com",
    "date": "2025-10-03",
    "subject": "Subject line",
    "body": "Full message contents"
  }
  ```
- **500 response**: `{"detail": "<client error message>"}` when the client fails to fetch.

### `POST /messages/{message_id}/mark-as-read`
Toggles the unread flag.
- **200 response**:
  ```json
  {
    "success": true,
    "message": "marked as read"
  }
  ```
- **500 response**:
  ```json
  {
    "detail": "Failed to mark message as read"
  }
  ```

### `DELETE /messages/{message_id}`
Deletes a message.
- **200 response**:
  ```json
  {
    "success": true,
    "message": "deleted"
  }
  ```
- **500 response**:
  ```json
  {
    "detail": "Failed to delete message"
  }
  ```

## Running the Service
```bash
uv run uvicorn mail_client_service:app --reload
curl "http://127.0.0.1:8000/messages?max_results=5"
```

## Testing
```bash
uv run pytest --no-cov src/mail_client_service/tests/test_routes.py
```

Tests override `get_mail_client` with fakes so the HTTP layer can be validated without hitting external providers; cache behaviour is covered explicitly via `reset_client_cache`.
