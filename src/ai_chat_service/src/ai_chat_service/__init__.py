# ai_chat_service/src/ai_chat_service/__init__.py

"""FastAPI service deployment package."""

from .main import app, auth_manager, get_current_user_id

__all__ = ["app", "auth_manager", "get_current_user_id"]
