# claude_chat_service/src/claude_chat_service/main.py


from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

# --- 1. Import from our "Contract" package (claude_chat_api) ---
# We use these Pydantic models to define our HTTP request/response shapes
from claude_chat_api import AbstractClaudeChatAPI, Message

# --- 2. Import from our "Implementation" package (claude_chat_impl) ---
# This is the "brain" and "auth logic"
from claude_chat_impl import AuthManager, ClaudeChatImplementation

# --- 3. Import from our "Service" package (this package) ---
# This is our security dependency
from .auth_deps import create_session_token, get_current_user_id

# --- 4. Create App and Logic Instances ---
app = FastAPI(
    title="Claude Chat Service",
    description="HW2 OSPD: Implements AI chat and OAuth 2.0",
    version="1.0.0",
    # This enables the /docs and /redoc UIs
    docs_url="/docs",
    redoc_url="/redoc",
)

# Instantiate our logic. In a real app, you might "inject"
# these using FastAPI's dependency system (e.g., as singletons).
impl: AbstractClaudeChatAPI = ClaudeChatImplementation()
auth_mgr = AuthManager()


# --- 5. Define Request Body Models ---
# This is for our single POST /chat endpoint
class ChatRequest(BaseModel):
    prompt: str


# Provide a simple landing page so hitting "/" is not a 404.
@app.get("/", include_in_schema=False)
async def landing() -> RedirectResponse:
    """Redirect the root URL to the interactive Swagger UI."""
    return RedirectResponse(url="/docs", status_code=status.HTTP_308_PERMANENT_REDIRECT)


# --- 6. Define Health Check Endpoint (Required by HW) ---
@app.get("/health", tags=["Monitoring"])
async def health_check():
    """Provides a simple HTTP 200 OK health check endpoint.
    """
    return {"status": "ok"}


# --- 7. Define OAuth 2.0 Endpoints (Required by HW) ---


@app.get("/auth/login", tags=["Authentication"])
async def login():
    """Step 1 of OAuth 2.0.
    Redirects the user's browser to the provider's login page.
    """
    auth_url = auth_mgr.get_authorization_url()
    return RedirectResponse(auth_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    # @app.get("/auth/callback", tags=["Authentication"])
    # async def auth_callback(request: Request, code: str):
    """
    Step 2 of OAuth 2.0.
    The provider redirects the user here. We exchange the 'code'
    for an 'access_token', get user info, and set a session cookie.
    """
    try:
        # 1. Exchange the code for an access token
        token_data = auth_mgr.exchange_code_for_tokens(code)
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(500, "Could not retrieve access token")

        # 2. Use the token to get the user's identity
        user_info = auth_mgr.get_user_info(access_token)
        user_id = user_info.get("email")  # Or 'sub', depending on provider

        if not user_id:
            raise HTTPException(500, "Could not retrieve user identifier")

        # 3. Create our own session token (JWT)
        session_token = create_session_token(user_id=user_id)

        # 4. Set the token in an HttpOnly cookie and redirect to /docs
        response = RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,  # Makes it inaccessible to JavaScript
            secure=False,  # Set to 'True' in production (HTTPS)
            samesite="lax",  # Good default for security
        )
        return response

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": f"OAuth processing failed: {e!s}"}
        )


# claude_chat_service/src/claude_chat_service/main.py

# Add 'Optional' to your 'from typing' import

# ... (rest of your imports)


@app.get("/auth/callback", tags=["Authentication"])
async def auth_callback(request: Request, code: str | None = None, error: str | None = None):
    """(Improved) Step 2 of OAuth 2.0.
    Handles the callback, checking for 'error' OR 'code'.
    """
    # Check if Google sent an error (e.g., redirect_uri_mismatch)
    if error:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": f"OAuth Error: {error}"})

    # If no error and no code, this is the FastAPI error you saw
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing 'code' query parameter")

    # --- (The rest of your function is the same) ---
    try:
        # 1. Exchange the code for an access token
        token_data = auth_mgr.exchange_code_for_tokens(code)
        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(500, "Could not retrieve access token")

        # 2. Use the token to get the user's identity
        user_info = auth_mgr.get_user_info(access_token)
        user_id = user_info.get("email")  # Or 'sub', depending on provider

        if not user_id:
            raise HTTPException(500, "Could not retrieve user identifier")

        # 3. Create our own session token (JWT)
        session_token = create_session_token(user_id=user_id)

        # 4. Set the token in an HttpOnly cookie and redirect to /docs
        response = RedirectResponse(url="/docs", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
        response.set_cookie(key="session_token", value=session_token, httponly=True, secure=False, samesite="lax")
        return response

    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": f"OAuth processing failed: {e!s}"}
        )


# --- 8. Define Protected API Endpoint (Our Minimal API) ---


@app.post("/chat", response_model=Message, tags=["Chat"])
async def send_chat_message(
    chat_request: ChatRequest,
    # This is the "security guard".
    # This dependency will run FIRST. If it fails (e.g., no cookie),
    # it will raise a 401 error and this endpoint code will
    # never even run. If it succeeds, it returns the user_id.
    current_user_id: str = Depends(get_current_user_id),
):
    """The main (and only) API endpoint for our minimal service.
    It takes a user's prompt and returns the AI's response.
    This endpoint is protected and requires a valid session token.
    """
    try:
        # The user is authenticated. We can now safely call our
        # implementation logic, passing in the authenticated user_id.
        ai_response = impl.send_message(prompt=chat_request.prompt, user_id=current_user_id)
        return ai_response
    except Exception as e:
        # This could be an APIError from Claude, etc.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred while processing your request: {e!s}"
        )
