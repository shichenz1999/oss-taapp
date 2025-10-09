import mail_client_api
import pytest

from mail_client_adapter.src.mail_client_adapter import register, ServiceMailClient


def test_register_overrides_get_client(monkeypatch):
    # before register, get_client is NotImplemented
    with pytest.raises(NotImplementedError):
        mail_client_api.get_client()

    register(base_url="http://example.com")

    client = mail_client_api.get_client()
    assert isinstance(client, ServiceMailClient)
