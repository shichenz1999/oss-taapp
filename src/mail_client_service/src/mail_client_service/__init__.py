"""FastAPI application entry point for the mail client service."""

from mail_client_service.main import app, get_mail_client, reset_client_cache

__all__ = ["app", "get_mail_client", "reset_client_cache"]
