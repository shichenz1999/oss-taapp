"""Outer package re-exports for src-layout convenience.

This lets consumers and tests do:

    from mail_client_adapter import ServiceMailClient, ServiceMessage, register

while the real code lives under src/mail_client_adapter/src/mail_client_adapter.
"""

from .src.mail_client_adapter import ServiceMailClient, ServiceMessage, register

__all__ = ["ServiceMailClient", "ServiceMessage", "register"]
