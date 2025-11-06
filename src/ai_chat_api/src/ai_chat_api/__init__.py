# src/ai_chat_api/__init__.py

"""Public export surface for ``ai_chat_api``."""

from . import client as _client_module
from . import message as _message_module

Client = _client_module.Client
Message = _message_module.Message
message = _message_module

__all__ = ["Client", "Message", "message", "get_client", "get_message"]