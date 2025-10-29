import json
import os
import urllib.parse
import webbrowser
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()  # Ensure .env values are available

CLIENT_ID = os.environ["GMAIL_CLIENT_ID"]
CLIENT_SECRET = os.environ["GMAIL_CLIENT_SECRET"]
SCOPE = os.environ["GMAIL_SCOPES"]
TOKEN_URI = os.environ["GMAIL_TOKEN_URI"]
REDIRECT_URI = "http://localhost:8080/oauth2callback"


def _write_token_json(refresh_token: str, access_token: str) -> None:
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
        "token": access_token,
        "token_uri": TOKEN_URI,
        "scopes": [SCOPE],
        "type": "authorized_user",
    }
    token_path = Path(__file__).resolve().parents[1] / "token.json"
    token_path.write_text(json.dumps(payload, indent=2))
    print(f"Saved token.json to {token_path}")


def _update_env(refresh_token: str) -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        print(f"WARNING: {env_path} not found; skipped updating .env.")
        return

    lines = env_path.read_text().splitlines()
    updated = False
    new_lines = []
    for line in lines:
        if line.startswith("GMAIL_REFRESH_TOKEN="):
            new_lines.append(f"GMAIL_REFRESH_TOKEN={refresh_token}")
            updated = True
        else:
            new_lines.append(line)
    if not updated:
        new_lines.append(f"GMAIL_REFRESH_TOKEN={refresh_token}")

    env_path.write_text("\n".join(new_lines) + "\n")
    print(f"Updated GMAIL_REFRESH_TOKEN in {env_path}")


def main() -> None:
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    print("Open this URL in your browser and authorize:\n", auth_url)
    webbrowser.open(auth_url)

    code = input("\nPaste the `code` from the redirect URL here: ").strip()
    if not code:
        raise SystemExit("No code provided.")

    response = requests.post(
        TOKEN_URI,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    print("\nToken response from Google:")
    print(json.dumps(payload, indent=2))

    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("No refresh_token returned; make sure access_type=offline and prompt=consent.")

    access_token = payload.get("access_token", "")

    _write_token_json(refresh_token, access_token)
    _update_env(refresh_token)
    print("Remember to copy the same refresh token into your CircleCI context.")


if __name__ == "__main__":
    main()
