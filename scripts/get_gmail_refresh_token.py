# get_gmail_refresh_token_simple.py
import json
import os
import urllib.parse
import webbrowser
import requests

CLIENT_ID = os.environ["GMAIL_CLIENT_ID"]
CLIENT_SECRET = os.environ["GMAIL_CLIENT_SECRET"]
REDIRECT_URI = "http://localhost:8080/oauth2callback"
SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


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
        "https://oauth2.googleapis.com/token",
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
    print("\nToken response (save the refresh_token safely):")
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()
