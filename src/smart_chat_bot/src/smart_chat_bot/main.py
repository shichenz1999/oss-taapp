from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from typing import Any, Iterable

from dotenv import load_dotenv
import claude_chat_impl  # noqa: F401  # ensure Claude registers ai_chat_api.get_ai_interface
import chat_client_api
import discord_client_impl  # noqa: F401  # ensure discord registers get_client
from ai_chat_api import AIInterface, get_ai_interface
from chat_client_api import ChatInterface, Message
from discord_client_impl.discord_impl import DiscordClient
from fastapi import FastAPI

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart_chat_bot")

CHAT_PROVIDER = os.environ.get("CHAT_PROVIDER", "discord")
CHANNEL_IDS: list[str] = [
    channel.strip()
    for channel in os.environ.get("CHAT_CHANNEL_IDS", "").split(",")
    if channel.strip()
]
if not CHANNEL_IDS:
    raise RuntimeError("CHAT_CHANNEL_IDS must list at least one channel id (comma-separated).")

POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "8"))
MAX_MESSAGES_PER_POLL = int(os.environ.get("MAX_MESSAGES_PER_POLL", "5"))
BOT_USER_ID = os.environ.get("BOT_USER_ID")  # optional: skip echoing own messages
SYSTEM_PROMPT = os.environ.get(
    "SMART_BOT_SYSTEM_PROMPT",
    "You are a concise, helpful assistant.",
)

app = FastAPI(
    title="Smart Chat Bot API",
    description="FastAPI service that polls chat provider, runs AI, and posts replies.",
    version="1.0.0",
)


# ---------------------------
# Helpers
# ---------------------------

async def _to_thread(func, *args, **kwargs):
    return await asyncio.to_thread(func, *args, **kwargs)


def make_chat_client(provider: str, **cfg: Any) -> ChatInterface:
    """Return a ChatInterface implementation based on the selected provider."""
    if provider == "discord":
        token = cfg.get("access_token") or os.environ.get("DISCORD_BOT_TOKEN")
        token_type = cfg.get("token_type") or os.environ.get("DISCORD_TOKEN_TYPE", "Bot")
        if token:
            return DiscordClient(access_token=token, token_type=token_type)
        return chat_client_api.get_client()

    msg = f"Unknown chat provider: {provider}"
    raise ValueError(msg)


async def fetch_recent_messages(client: ChatInterface, channel_id: str, limit: int) -> list[Message]:
    """Fetch recent messages (synchronously) in a thread."""
    return await _to_thread(client.get_messages, channel_id, limit=limit)


async def send_message(client: ChatInterface, channel_id: str, content: str) -> bool:
    """Send a message via the chat client in a thread."""
    return await _to_thread(client.send_message, channel_id, content)


async def generate_reply(ai: AIInterface, user_input: str) -> str:
    """Generate AI reply in a thread."""
    result = await _to_thread(ai.generate_response, user_input, SYSTEM_PROMPT, None)
    return result if isinstance(result, str) else str(result)


def _iter_new_messages(messages: Iterable[Message], last_seen_id: str | None) -> Iterable[Message]:
    """Yield messages that are newer than last_seen_id (messages ordered newest->oldest)."""
    for msg in messages:
        if last_seen_id and msg.id == last_seen_id:
            break
        yield msg


def is_bot_message(msg: Message) -> bool:
    raw = getattr(msg, "_raw_data", None)
    if isinstance(raw, dict):
        author = raw.get("author")
        return isinstance(author, dict) and bool(author.get("bot"))
    return False


# ---------------------------
# Polling loop
# ---------------------------

async def _handle_channel(
    client: ChatInterface,
    ai: AIInterface,
    channel_id: str,
    last_seen: dict[str, str],
) -> None:
    try:
        messages = await fetch_recent_messages(client, channel_id, MAX_MESSAGES_PER_POLL)
        logger.info("Fetched %d messages from channel %s", len(messages), channel_id)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to fetch messages for channel %s: %s", channel_id, exc)
        return

    for msg in _iter_new_messages(messages, last_seen.get(channel_id)):
        content_str = str(msg.content or "")
        logger.info(
            "Considering message %s from %s (len=%d)",
            msg.id,
            msg.sender_id,
            len(content_str),
        )
        if is_bot_message(msg):
            logger.info("Skip bot message %s in channel %s", msg.id, channel_id)
            continue
        if not content_str.strip():
            # Skip empty/blank messages to avoid 400 from AI provider.
            last_seen[channel_id] = msg.id
            logger.info(
                "Skip empty message %s in channel %s content=%r",
                msg.id,
                channel_id,
                content_str,
            )
            continue
        try:
            reply = await generate_reply(ai, content_str)
            await send_message(client, channel_id, reply)
            last_seen[channel_id] = msg.id
            logger.info("Replied to message %s in channel %s", msg.id, channel_id)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to handle message %s in channel %s: %s", msg.id, channel_id, exc)


async def _poll_loop() -> None:
    """Background poller: get new messages, run AI, reply."""
    client = make_chat_client(CHAT_PROVIDER)
    ai = get_ai_interface()
    last_seen: dict[str, str] = {}

    logger.info(
        "Poll loop started | provider=%s | channels=%s | interval=%ss",
        CHAT_PROVIDER,
        CHANNEL_IDS,
        POLL_INTERVAL_SECONDS,
    )

    while True:
        for channel_id in CHANNEL_IDS:
            await _handle_channel(client, ai, channel_id, last_seen)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


# ---------------------------
# FastAPI lifecycle
# ---------------------------

@app.on_event("startup")
async def start_polling() -> None:
    """Kick off the background poller when the service starts."""
    app.state.polling_task = asyncio.create_task(_poll_loop())
    logger.info("Smart chat bot started.")


@app.on_event("shutdown")
async def stop_polling() -> None:
    """Cancel the background poller when the service stops."""
    task = getattr(app.state, "polling_task", None)
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


@app.get("/", tags=["General"])
async def root() -> dict[str, object]:
    """Basic heartbeat for the smart chat bot service."""
    return {
        "status": "ok",
        "provider": CHAT_PROVIDER,
        "channels": CHANNEL_IDS,
        "poll_interval_seconds": POLL_INTERVAL_SECONDS,
    }
