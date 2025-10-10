# Generating a Gmail Refresh Token

This guide walks through creating or refreshing the long-lived Gmail OAuth refresh token used by local development and CI.

## Prerequisites

1. Gmail API enabled in your Google Cloud project.
2. OAuth client (Desktop application or Web) whose **Authorized redirect URI** includes `http://localhost:8080/oauth2callback`.
3. Project root contains:
   - `credentials.json` downloaded from Google Cloud.
   - `.env` file with the following keys (values from your OAuth client):

     ```bash
     GMAIL_CLIENT_ID=xxxx.apps.googleusercontent.com
     GMAIL_CLIENT_SECRET=xxxx
     GMAIL_SCOPES=https://mail.google.com/
     GMAIL_TOKEN_URI=https://oauth2.googleapis.com/token
     GMAIL_UNIVERSE_DOMAIN=googleapis.com
     # Optional; defaults to http://localhost:8080/oauth2callback if omitted
     GMAIL_REDIRECT_URI=http://localhost:8080/oauth2callback
     ```

## Run the helper script

1. Execute the helper that reads credentials directly from `.env`:

   ```bash
   uv run python scripts/get_gmail_refresh_token.py
   ```

2. When the browser opens, sign in with a user who has access to the OAuth consent screen.
3. Approve the requested permissions. You will be redirected to `localhost` (the page will likely show an error—this is expected).
4. Copy the `code=...` value from the browser's URL bar and paste it back into the terminal when prompted.
5. The script prints the raw JSON response, writes a normalized `token.json` in the project root, and updates `GMAIL_REFRESH_TOKEN=...` inside `.env` if it exists (no backup is created).

## Store the refresh token

1. **Confirm `.env`:**
   The helper overwrote `GMAIL_REFRESH_TOKEN` for you. If `.env` did not exist, create it and add the key manually.

2. **Verify `token.json`:**
   The helper overwrote `token.json` automatically. Confirm the fields match your `client_id`, `client_secret`, and scope (`https://mail.google.com/`).

## CircleCI context

Mirror the six `GMAIL_*` variables in a CircleCI context (e.g., `gmail-client`). Whenever you refresh the token locally, update the context so CI integration jobs continue to pass.
