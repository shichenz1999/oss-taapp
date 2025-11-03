"""FastAPI deployment unit for the Claude chat service."""

from __future__ import annotations

import logging
from typing import Annotated

import anthropic
import httpx
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from claude_chat_api import AbstractClaudeChatAPI, Message
from claude_chat_impl import AuthManager, ClaudeChatImplementation

from .auth_deps import create_session_token, get_current_user_id

LOGGER = logging.getLogger(__name__)

app = FastAPI(
    title="Claude Chat Service",
    description="HW2 OSPD: Implements AI chat and OAuth 2.0",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

impl: AbstractClaudeChatAPI = ClaudeChatImplementation()
auth_mgr = AuthManager()


class ChatRequest(BaseModel):
    """Request payload accepted by the chat endpoint."""

    prompt: str


@app.get("/", include_in_schema=False)
async def landing() -> RedirectResponse:
    """Redirect root requests to the interactive documentation."""
    return RedirectResponse(url="/docs", status_code=status.HTTP_308_PERMANENT_REDIRECT)


@app.get("/health", tags=["Monitoring"])
async def health_check() -> dict[str, str]:
    """Return a simple health status payload."""
    return {"status": "ok"}


@app.get("/auth/login", tags=["Authentication"])
async def login() -> RedirectResponse:
    """Start the OAuth flow by redirecting the browser to the provider."""
    auth_url = auth_mgr.get_authorization_url()
    return RedirectResponse(auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/auth/callback", tags=["Authentication"])
async def auth_callback(code: str | None = None, error: str | None = None) -> Response:
    """Handle the OAuth callback, establish a session cookie, and redirect to docs."""
    if error:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"OAuth error: {error}"},
        )

    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'code' query parameter")

    try:
        token_data = auth_mgr.exchange_code_for_tokens(code)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth token exchange failed",
        ) from exc

    access_token = token_data.get("access_token")
    if not isinstance(access_token, str):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Could not retrieve access token")

    try:
        user_info = auth_mgr.get_user_info(access_token)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user information",
        ) from exc

    user_id_raw = user_info.get("email") or user_info.get("sub")
    if not isinstance(user_id_raw, str):
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "Could not retrieve user identifier")

    session_token = create_session_token(user_id=user_id_raw)
    response = RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,
        samesite="lax",
    )
    return response


@app.post("/chat", response_model=Message, tags=["Chat"])
async def send_chat_message(
    chat_request: ChatRequest,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
) -> Message:
    """Forward the prompt to Claude and return the assistant response."""
    try:
        return impl.send_message(prompt=chat_request.prompt, user_id=current_user_id)
    except anthropic.APIError as exc:
        LOGGER.exception("Claude API call failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request.",
        ) from exc
