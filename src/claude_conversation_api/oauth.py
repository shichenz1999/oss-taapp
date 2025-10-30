# main.py
import os
import time
import requests
from urllib.parse import urlencode
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from dotenv import load_dotenv

# load google oauth setup
load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") # claude api key

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

app = FastAPI()

# user tokens database
USER_TOKENS = {}  # { email: {access_token, refresh_token, expires_at} }


@app.get("/login")
def login():
    """login: redirect to google authentication"""
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": REDIRECT_URI,
        "access_type": "offline",  # request refresh_token
        "prompt": "consent",       # Force the display of the authorization page (ensure that the refresh_token can be obtained)
    }
    url = AUTH_URL + "?" + urlencode(params)
    return RedirectResponse(url)


@app.get("/auth/callback")
def auth_callback(request: Request):
    """callback endpoint: get access_token/refresh_token"""
    code = request.query_params.get("code")
    if not code:
        return JSONResponse({"error": "missing code"}, status_code=400)

    data = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    resp = requests.post(TOKEN_URL, data=data)
    token_data = resp.json()

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in") 
    expires_at = int(time.time()) + expires_in

    # userinfo
    userinfo = requests.get(
        USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()
    email = userinfo.get("email")

    USER_TOKENS[email] = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at
    }

    return JSONResponse({"message": f"User {email} authenticated successfully"})


def refresh_access_token(email: str):
    """refresh access token"""
    tokens = USER_TOKENS.get(email)
    if not tokens or not tokens.get("refresh_token"):
        raise Exception("No refresh token found for user")

    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": tokens["refresh_token"],
        "grant_type": "refresh_token",
    }

    resp = requests.post(TOKEN_URL, data=data)
    if resp.status_code != 200:
        raise Exception(f"Failed to refresh token: {resp.text}")

    new_data = resp.json()
    new_access_token = new_data["access_token"]
    expires_in = new_data.get("expires_in", 3600)
    new_expires_at = int(time.time()) + expires_in

    # update user token
    USER_TOKENS[email]["access_token"] = new_access_token
    USER_TOKENS[email]["expires_at"] = new_expires_at

    print(f"Refreshed access_token for {email}")
    return new_access_token


# check/get valid access token
def get_valid_access_token(email: str):
    tokens = USER_TOKENS.get(email)
    if not tokens:
        raise Exception("User not authenticated")

    # if access_token expire
    if int(time.time()) >= tokens["expires_at"]:
        return refresh_access_token(email)

    return tokens["access_token"]


# use claude api
@app.post("/chat")
def chat(request: Request):
    email = request.query_params.get("email")
    if email not in USER_TOKENS:
        return JSONResponse({"error": "User not logged in"}, status_code=401)

    try:
        if email is None:
            return JSONResponse({"error": "User email is null"}, status_code=400)
        _ = get_valid_access_token(email) 
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    # 调用 Claude API
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "你好 Claude，这是一条测试消息"}],
    }

    claude_resp = requests.post(CLAUDE_API_URL, headers=headers, json=data)
    return claude_resp.json()
