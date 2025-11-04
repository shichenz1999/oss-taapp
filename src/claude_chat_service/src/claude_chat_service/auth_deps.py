# claude_chat_service/src/claude_chat_service/auth_deps.py


# We can import from 'claude_chat_impl' because it's
# installed as a local dependency via pyproject.toml
from claude_chat_impl.settings import settings
from fastapi import HTTPException, Request, status
from jose import JWTError, jwt


def get_current_user_id(request: Request) -> str:
    """A FastAPI dependency that reads the session_token cookie,
    validates the JWT, and returns the user_id (from the 'sub' claim).
    
    If the token is invalid or missing, it raises an HTTP 401 error.
    """
    # 1. Read the token from the cookie
    token = request.cookies.get("session_token")

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated (Missing session cookie)",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 2. Decode and validate the JWT
        payload = jwt.decode(
            token,
            settings.SESSION_SECRET_KEY,
            algorithms=[settings.SESSION_ALGORITHM]
        )

        # 3. Extract the user_id (which we store in the 'sub' claim)
        user_id: str | None = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        # This catches invalid signatures, expired tokens, etc.
        raise credentials_exception

    # 4. Return the user_id for the endpoint to use
    return user_id

def create_session_token(user_id: str) -> str:
    """Creates a new JWT (session token) for the given user_id.
    
    Args:
        user_id: The user's unique identifier (e.g., their email).
    
    Returns:
        A signed JWT string.

    """
    to_encode = {"sub": user_id}

    # (Optional) You can add an expiry time ('exp') here
    # from datetime import datetime, timedelta, timezone
    # expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    # to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SESSION_SECRET_KEY,
        algorithm=settings.SESSION_ALGORITHM
    )
    return encoded_jwt
