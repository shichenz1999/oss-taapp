from fastapi import HTTPException, Request, status
from jose import JWTError, jwt

from .settings import settings


def get_current_user_id(request: Request) -> str:
    """Return the authenticated user ID from the session cookie."""
    token = request.cookies.get("session_token")
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please log in to send messages.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.SESSION_SECRET_KEY, algorithms=[settings.SESSION_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


def create_session_token(user_id: str) -> str:
    """Issue a signed JWT storing the given user ID."""
    return jwt.encode({"sub": user_id}, settings.SESSION_SECRET_KEY, algorithm=settings.SESSION_ALGORITHM)
