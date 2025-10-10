# tests/e2e/test_mail_client_service.py
import os
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

import mail_client_adapter
import mail_client_api

pytestmark = pytest.mark.e2e

SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 8765
BASE_URL = f"http://{SERVICE_HOST}:{SERVICE_PORT}"


@contextmanager
def run_service() -> Iterator[str]:
    app_dir = Path(__file__).resolve().parents[2] / "src" / "mail_client_service"
    env = os.environ.copy()
    process = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "uvicorn",
            "mail_client_service:app",
            "--host",
            SERVICE_HOST,
            "--port",
            str(SERVICE_PORT),
        ],
        cwd=str(app_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        _wait_for_port(SERVICE_HOST, SERVICE_PORT)
        yield BASE_URL
    finally:
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def _wait_for_port(host: str, port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket() as sock:
            sock.settimeout(1.0)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.2)
    raise RuntimeError(f"Service on {host}:{port} did not start within {timeout}s")


@pytest.mark.local_credentials
def test_service_roundtrip() -> None:
    workspace = Path(__file__).resolve().parents[2]
    credentials = workspace / "credentials.json"
    token = workspace / "token.json"
    if not credentials.exists() and not token.exists():
        pytest.skip("No credentials/token found for live Gmail E2E")

    with run_service() as base_url:
        mail_client_adapter.register(base_url=base_url)
        client = mail_client_api.get_client(interactive=False)

        messages = list(client.get_messages(max_results=1))
        assert messages, "Expected at least one message from live Gmail API"

        first_id = messages[0].id
        detailed = client.get_message(first_id)
        assert detailed.id == first_id
        assert detailed.subject is not None
