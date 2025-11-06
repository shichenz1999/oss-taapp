from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# Importing claude_chat_impl triggers registration of the concrete implementation.
import claude_chat_impl  # noqa: F401
from ai_chat_api import Client, get_client
from claude_chat_impl import AuthManager

from .auth_deps import create_session_token, get_current_user_id

app = FastAPI()

auth_manager = AuthManager()


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    role: str
    content: str


@app.get("/", include_in_schema=False)
async def landing() -> RedirectResponse:
    return RedirectResponse(url="/docs", status_code=status.HTTP_308_PERMANENT_REDIRECT)


@app.get("/health", tags=["Monitoring"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/auth/login", tags=["Authentication"])
async def login() -> RedirectResponse:
    return RedirectResponse(auth_manager.get_authorization_url(), status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/auth/callback", tags=["Authentication"])
async def auth_callback(code: str | None = None, error: str | None = None) -> RedirectResponse:
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


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def send_chat_message(
    chat_request: ChatRequest,
    current_user_id: str = Depends(get_current_user_id),
    chat_client: Client = Depends(get_client),
) -> ChatResponse:
    message = chat_client.send_message(prompt=chat_request.prompt, user_id=current_user_id)
    return ChatResponse(role=message.role, content=message.content)
