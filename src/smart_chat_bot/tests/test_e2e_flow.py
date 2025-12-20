"""End-to-end flow test for smart_chat_bot using real services."""

from __future__ import annotations

import os

import pytest
from ai_chat_api import get_ai_interface


def _split_channel_ids(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


_required_env = [
    "CHAT_CHANNEL_IDS",
    "DISCORD_BOT_TOKEN",
    "ANTHROPIC_API_KEY",
    "JIRA_API_TOKEN",
    "JIRA_API_EMAIL",
    "TICKET_PROJECT_KEY",
]
_missing = [key for key in _required_env if not os.environ.get(key)]
if not (os.environ.get("JIRA_API_BASE") or os.environ.get("JIRA_CLOUD_ID")):
    _missing.append("JIRA_API_BASE or JIRA_CLOUD_ID")
if not _split_channel_ids(os.environ.get("CHAT_CHANNEL_IDS")) and "CHAT_CHANNEL_IDS" not in _missing:
    _missing.append("CHAT_CHANNEL_IDS")
if _missing:
    pytest.skip(
        f"Missing required env vars for smart_chat_bot e2e: {sorted(set(_missing))}",
        allow_module_level=True,
    )

from smart_chat_bot import main  # noqa: E402  # skip check runs before import

pytestmark = [pytest.mark.e2e, pytest.mark.local_credentials]

DEFAULT_E2E_PROMPT = "Hello! Please reply with a short greeting only."


@pytest.mark.asyncio
async def test_full_flow_real_services() -> None:
    """Chat -> AI -> TicketImpl -> reply using real services."""
    channel_id = main.CHANNEL_IDS[0]
    prompt = DEFAULT_E2E_PROMPT

    client = main.make_chat_client(main.CHAT_PROVIDER)
    ai = get_ai_interface()

    messages = await main.fetch_recent_messages(
        client,
        channel_id,
        limit=main.MAX_MESSAGES_PER_POLL,
    )
    for msg in messages:
        content = str(msg.content or "").strip()
        if not content:
            continue
        if main.is_bot_message(msg):
            continue
        prompt = content
        break

    action = await main.generate_bot_action(ai, prompt)
    reply = await main.execute_ticket_action(action)
    sent = await main.send_message(client, channel_id, reply)

    assert sent is True
