"""Smart chat bot service: polls chat provider, calls AI, posts replies."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
from importlib import import_module
from typing import TYPE_CHECKING, TypeVar

from discord_client_impl.discord_impl import DiscordClient
from dotenv import load_dotenv
from fastapi import FastAPI
from ticket_api.adapter import StandardizedTicketAdapter
from ticket_api.shared_interface import TicketInterface, TicketStatus

import chat_client_api
import claude_chat_impl  # noqa: F401  # ensure Claude registers ai_chat_api.get_ai_interface
import discord_client_impl  # noqa: F401  # ensure discord registers get_client
from ai_chat_api import AIInterface, get_ai_interface
from chat_client_api import ChatInterface, Message
from smart_chat_bot.prompts import TICKET_SYSTEM_PROMPT
from smart_chat_bot.schemas import BotAction, TicketIntent

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

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
    missing_channels_msg = "CHAT_CHANNEL_IDS must list at least one channel id."
    raise RuntimeError(missing_channels_msg)

POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "8"))
MAX_MESSAGES_PER_POLL = int(os.environ.get("MAX_MESSAGES_PER_POLL", "5"))
BOT_USER_ID = os.environ.get("BOT_USER_ID")

app = FastAPI(title="Smart Chat Bot API", version="1.0.0")

def _make_ticket_service() -> TicketInterface:
    """Build the ticket service factory; swappable via env."""
    impl_path = os.environ.get("TICKET_PROVIDER_IMPL", "ticket_impl:TicketImpl")
    user = os.environ.get("TICKET_USER_ID", "bot-user")
    project = os.environ.get("TICKET_PROJECT_KEY", "TEST")

    module_name, class_name = impl_path.split(":")
    module = import_module(module_name)
    impl_cls = getattr(module, class_name)
    internal = impl_cls(user_id=user, project_key=project)
    return StandardizedTicketAdapter(internal, reporter=user)


# --- Initialize Ticket Service ---
ticket_service: TicketInterface = _make_ticket_service()

# ---------------------------
# Helpers
# ---------------------------

T = TypeVar("T")

async def _to_thread(func: Callable[..., T], *args: object, **kwargs: object) -> T:
    return await asyncio.to_thread(func, *args, **kwargs)

def make_chat_client(provider: str, **cfg: str | None) -> ChatInterface:
    """Return a ChatInterface implementation based on the provider."""
    if provider == "discord":
        token = cfg.get("access_token") or os.environ.get("DISCORD_BOT_TOKEN")
        token_type = cfg.get("token_type") or os.environ.get("DISCORD_TOKEN_TYPE", "Bot")
        if token:
            return DiscordClient(access_token=token, token_type=token_type)
        return chat_client_api.get_client()
    err = f"Unknown chat provider: {provider}"
    raise ValueError(err)

async def fetch_recent_messages(client: ChatInterface, channel_id: str, limit: int) -> list[Message]:
    """Fetch recent messages from a channel."""
    return await _to_thread(client.get_messages, channel_id, limit=limit)

async def send_message(client: ChatInterface, channel_id: str, content: str) -> bool:
    """Send a message to a channel."""
    return await _to_thread(client.send_message, channel_id, content)


BOT_ACTION_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "intent": {
            "type": "string",
            "enum": [
                "create_ticket",
                "get_ticket",
                "search_tickets",
                "update_ticket",
                "delete_ticket",
                "chat",
            ],
        },
        "params": {"type": "object"},
    },
    "required": ["intent", "params"],
    "additionalProperties": False,
}


def _safe_status(value: str | None) -> TicketStatus | None:
    """Convert a string to TicketStatus, logging and ignoring invalid values."""
    if not value:
        return None
    try:
        return TicketStatus(value)
    except ValueError:
        logger.warning("Invalid status value from AI: %r", value)
        return None


async def generate_bot_action(ai: AIInterface, user_input: str) -> BotAction:
    """Call AI and parse the JSON response into a BotAction."""
    raw_response = await _to_thread(
        ai.generate_response, user_input, TICKET_SYSTEM_PROMPT, BOT_ACTION_SCHEMA
    )

    # Normalize to string then attempt JSON parse; fall back to dict path.
    if isinstance(raw_response, dict):
        try:
            return BotAction.model_validate(raw_response)
        except (ValueError, TypeError) as exc:
            logger.warning("BotAction validation failed on dict (%s). Raw: %s", exc, raw_response)
            return BotAction(intent=TicketIntent.CHAT, params={"message": str(raw_response)})

    clean_json = str(raw_response).strip()
    if clean_json.startswith("```"):
        clean_json = clean_json.split("\n", 1)[-1].rsplit("\n", 1)[0]

    try:
        return BotAction.model_validate_json(clean_json)
    except (ValueError, TypeError) as exc:
        try:
            parsed = json.loads(clean_json)
            return BotAction.model_validate(parsed)
        except (ValueError, TypeError):
            logger.warning("JSON parse failed (%s). Raw: %s", exc, raw_response)
            return BotAction(intent=TicketIntent.CHAT, params={"message": str(raw_response)})


async def execute_ticket_action(action: BotAction) -> str:  # noqa: C901, PLR0911, PLR0912
    """Routes the intent to the ticket service."""
    p = action.params

    try:
        if action.intent == TicketIntent.CREATE_TICKET:
            # Handle Priority Injection
            title = p.get("title")
            desc = p.get("description", "")
            if not title:
                return "❌ Missing title for ticket creation."
            if prio := p.get("priority"):
                desc = f"[{prio.upper()}] {desc}".strip()
            t = await _to_thread(ticket_service.create_ticket, title, desc, p.get("assignee"))
            return f"✅ Ticket Created! ID: {t.id} "

        if action.intent == TicketIntent.GET_TICKET:
            ticket_id = p.get("ticket_id")
            if not ticket_id:
                return "❌ ticket_id is required."
            t = await _to_thread(ticket_service.get_ticket, ticket_id)
            return f"📄 Ticket {t.id}: {t.title} ({t.status})" if t else "❌ Ticket not found."

        if action.intent == TicketIntent.SEARCH_TICKETS:
            # Handle Enum Conversion
            status = _safe_status(p.get("status"))
            tickets = await _to_thread(ticket_service.search_tickets, p.get("query"), status)
            if not tickets:
                return "🔍 No tickets found."
            return "🔍 Results:\n" + "\n".join([f"- [{t.id}] {t.status}: {t.title}" for t in tickets])

        if action.intent == TicketIntent.UPDATE_TICKET:
            status = _safe_status(p.get("status"))
            ticket_id = p.get("ticket_id")
            if not ticket_id:
                return "❌ ticket_id is required."
            t = await _to_thread(ticket_service.update_ticket, ticket_id, status, p.get("title"))
            return f"✅ Ticket {t.id} updated. Status: {t.status} "

        if action.intent == TicketIntent.DELETE_TICKET:
            ticket_id = p.get("ticket_id")
            if not ticket_id:
                return "❌ ticket_id is required."
            ok = await _to_thread(ticket_service.delete_ticket, ticket_id)
            return f"🗑️ Ticket {p['ticket_id']} deleted." if ok else "❌ Delete failed."

        if action.intent == TicketIntent.CHAT:
            return p.get("message", "...")

    except Exception as exc:
        logger.exception("Action failed")
        return f"⚠️ Error executing {action.intent}: {exc}"

    return "Error: Unknown intent."

def _iter_new_messages(messages: Iterable[Message], last_seen_id: str | None) -> Iterable[Message]:
    for msg in messages:
        if last_seen_id and msg.id == last_seen_id:
            break
        yield msg

def is_bot_message(msg: Message) -> bool:
    """Return True if the message author is marked as a bot."""
    raw = getattr(msg, "_raw_data", None)
    if isinstance(raw, dict):
        author = raw.get("author")
        return isinstance(author, dict) and bool(author.get("bot"))
    return False

# ---------------------------
# Polling loop
# ---------------------------

async def _handle_channel(client: ChatInterface, ai: AIInterface, channel_id: str, last_seen: dict[str, str]) -> None:
    try:
        messages = await fetch_recent_messages(client, channel_id, MAX_MESSAGES_PER_POLL)
        logger.info("Fetched %d messages from channel %s", len(messages), channel_id)
    except Exception:
        logger.exception("Failed to fetch messages for channel %s", channel_id)
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
            last_seen[channel_id] = msg.id
            logger.info(
                "Skip empty message %s in channel %s content=%r",
                msg.id,
                channel_id,
                content_str,
            )
            continue

        try:
            # 1. AI Analysis
            bot_action = await generate_bot_action(ai, content_str)
            logger.info("Intent: %s", bot_action.intent)

            # 2. Execution & Reply
            reply_text = await execute_ticket_action(bot_action)
            await send_message(client, channel_id, reply_text)

            last_seen[channel_id] = msg.id
        except Exception:
            logger.exception("Failed to handle message %s", msg.id)

async def _poll_loop() -> None:
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
        tasks = [asyncio.create_task(_handle_channel(client, ai, cid, last_seen)) for cid in CHANNEL_IDS]
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)

# ---------------------------
# FastAPI lifecycle
# ---------------------------

@app.on_event("startup")
async def start_polling() -> None:
    """Start the background polling loop."""
    app.state.polling_task = asyncio.create_task(_poll_loop())
    logger.info("Smart chat bot started.")

@app.on_event("shutdown")
async def stop_polling() -> None:
    """Stop the background polling loop."""
    task = getattr(app.state, "polling_task", None)
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


@app.get("/", tags=["General"])
async def root() -> dict[str, object]:
    """Return basic heartbeat for the smart chat bot service."""
    return {
        "status": "ok",
        "provider": CHAT_PROVIDER,
        "channels": CHANNEL_IDS,
        "poll_interval_seconds": POLL_INTERVAL_SECONDS,
    }
