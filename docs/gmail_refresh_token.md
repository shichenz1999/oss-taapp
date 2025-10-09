# Generating a Gmail Refresh Token

## Prerequisites
- Gmail API enabled in your Google Cloud project.
- OAuth client with `http://localhost:8080/oauth2callback` configured as an authorized redirect URI.
- Local `.env` (from `config.example.env`) containing `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET`.

## Run the helper
1. `uv run python scripts/get_gmail_refresh_token.py`
2. When the browser opens, sign in with an account listed under **OAuth consent screen → Test users**.
3. Ignore the “localhost refused to connect” page; copy the `code=...` value from the address bar.
4. Paste that code back into the terminal; the script prints a JSON payload.

## Store the secret
- Append the returned `refresh_token` to `.env`:
