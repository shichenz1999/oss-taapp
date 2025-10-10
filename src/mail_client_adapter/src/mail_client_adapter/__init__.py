"""Public exports for the mail_client_adapter package."""

import mail_client_api

from .client_adapter import ServiceMailClient
from .message_adapter import ServiceMessage

__all__ = ["ServiceMailClient", "ServiceMessage", "register"]


def register(*, base_url: str) -> None:
    """Let mail_client_api.get_client return the service-backed implementation."""

    def _factory(*, interactive: bool = False) -> mail_client_api.Client:
        _ = interactive  # keep signature compatible; not used in this implementation
        return ServiceMailClient(base_url=base_url)

    mail_client_api.get_client = _factory
