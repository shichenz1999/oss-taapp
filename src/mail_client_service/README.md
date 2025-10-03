# mail_client_service Skeleton

This package hosts the FastAPI wrapper around the shared `mail_client_api` and Gmail implementation packages. The current branch only ships the service skeleton so teammates can implement each endpoint independently.

## Structure
- `src/mail_client_service/src/mail_client_service/__init__.py`: FastAPI application plus shared helpers (`get_mail_client`, `_serialize_message`) with `NotImplementedError` placeholders for each route.
- `src/mail_client_service/tests/test_routes.py`: Pytest skeleton that overrides the mail client dependency and skips each endpoint test until it is implemented.

## Expected Endpoints
Implementations must provide thin wrappers over `mail_client_api.Client`:
- `GET /messages` → list message summaries (id, from, to, date, subject).
- `GET /messages/{message_id}` → return the full message (`_serialize_message`).
- `POST /messages/{message_id}/mark-as-read` → call `mark_as_read` and return `{"status": "read"}` or an error.
- `DELETE /messages/{message_id}` → call `delete_message` and return `{"status": "deleted"}` or an error.

## Development Workflow
1. Create a feature branch per endpoint (e.g. `feature/messages-list`).
2. Replace the relevant `NotImplementedError` with real logic, reusing `mail_client_api.get_client()` exclusively.
3. Update the matching test in `tests/test_routes.py` and remove the `pytest.skip`.
4. Run `uv run pytest src/mail_client_service/tests/test_routes.py` before opening a PR.
5. Submit a pull request referencing the endpoint issue and request peer review.

## Notes
- Keep the service a thin adapter: do not duplicate message parsing or Gmail-specific logic—delegate to `mail_client_api`/`gmail_client_impl`.
- When adding shared utilities, coordinate with the team so everyone reuses the same helpers.
