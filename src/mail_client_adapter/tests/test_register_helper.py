import mail_client_api
import pytest

from mail_client_adapter import ServiceMailClient, register


def test_register_overrides_get_client(monkeypatch):
    """Ensure our register() swaps the global factory to ServiceMailClient."""

    def _sentinel(*, interactive: bool = False):
        raise NotImplementedError

    # Reset mail_client_api.get_client to a known sentinel so Gmail's auto-registration
    # (triggered elsewhere in the suite) can't interfere with this unit test.
    monkeypatch.setattr(mail_client_api, "get_client", _sentinel, raising=False)

    with pytest.raises(NotImplementedError):
        mail_client_api.get_client()

    register(base_url="http://example.com")

    client = mail_client_api.get_client()
    assert isinstance(client, ServiceMailClient)
