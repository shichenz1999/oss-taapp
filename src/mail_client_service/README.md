# Mail Client Service

## Overview
`mail_client_service` wraps a FastAPI application around the `mail_client_api.Client` contract so mailbox capabilities are reachable over HTTP. The package binds whichever concrete client is registered (for example `gmail_client_impl`) and translates requests into method calls on that client.

## Responsibilities
- Serve HTTP routes for core mailbox actions (list, fetch, mark-as-read, delete).
- Serialise `mail_client_api.Message` instances into consistent JSON payloads.
- Provide a dependency hook (`get_mail_client`) so tests or alternative adapters can swap the client implementation.

## Key Modules
- `src/mail_client_service/src/mail_client_service/__init__.py`: exports the FastAPI `app`, dependency factory, and route handlers.
- `src/mail_client_service/tests/test_routes.py`: validates success and error paths by overriding `get_mail_client` with mocks.

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

Tests override `get_mail_client` to exercise the routes without hitting external providers.
