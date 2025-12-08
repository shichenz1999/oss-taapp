"""FastAPI application exposing the AI chat endpoints."""

from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# Importing claude_chat_impl triggers registration of the concrete implementation.
import claude_chat_impl  # noqa: F401
from ai_chat_api import AIInterface, AIStructuredResponse, get_ai_interface

from .auth_deps import create_session_token
from .auth_deps import get_current_user_id as auth_get_current_user_id
from .auth_manager import AuthManager

app = FastAPI()

auth_manager = AuthManager()
get_current_user_id = auth_get_current_user_id


class ChatRequest(BaseModel):
    """Inbound payload carrying a single chat prompt."""

    user_input: str
    system_prompt: str
    response_schema: dict[str, Any] | None = None


@app.get("/", include_in_schema=False)
async def landing() -> RedirectResponse:
    """Redirect root requests to the generated docs."""
    return RedirectResponse(url="/docs", status_code=status.HTTP_308_PERMANENT_REDIRECT)


@app.get("/health", tags=["Monitoring"])
async def health_check() -> dict[str, str]:
    """Return an operational heartbeat."""
    return {"status": "ok"}


@app.get("/auth/login", tags=["Authentication"])
async def login() -> RedirectResponse:
    """Kick off OAuth login flow."""
    return RedirectResponse(auth_manager.get_authorization_url(), status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/auth/logout", tags=["Authentication"])
async def logout() -> RedirectResponse:
    """Clear the session cookie and redirect to docs."""
    response = RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.delete_cookie(key="session_token", httponly=True, secure=False, samesite="lax")
    return response


@app.get("/auth/callback", tags=["Authentication"])
async def auth_callback(code: str | None = None, error: str | None = None) -> RedirectResponse:
    """Handle OAuth callback responses to establish a session."""
    if error is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"OAuth Error: {error}")
    if code is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'code' query parameter")

    token_payload = auth_manager.exchange_code_for_tokens(code)
    access_token = token_payload.get("access_token")
    if access_token is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve access token")

    user_info = auth_manager.get_user_info(access_token)
    user_id = user_info.get("email")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve user identifier")

    session_token = create_session_token(user_id=user_id)
    response = RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    response.set_cookie(key="session_token", value=session_token, httponly=True, secure=False, samesite="lax")
    return response


@app.post("/chat", tags=["Chat"], response_model=AIStructuredResponse)
async def send_chat_message(
    chat_request: ChatRequest,
    current_user_id: Annotated[str, Depends(get_current_user_id)],
    chat_client: Annotated[AIInterface, Depends(get_ai_interface)],
) -> AIStructuredResponse:
    """Forward prompts to the configured ai_chat_api client."""
    response = chat_client.generate_response(
        user_input=chat_request.user_input,
        system_prompt=chat_request.system_prompt,
        response_schema=chat_request.response_schema,
    )

    if isinstance(response, AIStructuredResponse):
        return response

    return AIStructuredResponse(intent="chat", message=str(response), parameters={})
