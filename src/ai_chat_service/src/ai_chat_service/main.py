"""FastAPI application exposing health check and chat endpoints."""

from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Response, status
from pydantic import BaseModel

import claude_chat_impl  # noqa: F401  # ensure AI implementation registers itself
from ai_chat_api import AIInterface
from ai_chat_api import get_ai_interface as _get_ai_interface
from ai_chat_service.telemetry import PrometheusMiddleware, get_metrics

app = FastAPI()

app.add_middleware(PrometheusMiddleware)


def get_ai_interface() -> AIInterface:
    """Expose the currently registered AI interface factory to FastAPI."""
    return _get_ai_interface()


class ChatRequest(BaseModel):
    """Inbound payload carrying a single chat prompt."""

    user_input: str
    system_prompt: str | None = None
    response_schema: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    """Standardized chat response mirroring ai_chat_api output."""

    response: str | dict[str, Any]


@app.get("/health", tags=["Monitoring"])
async def health_check() -> dict[str, str]:
    """Return an operational heartbeat."""
    return {"status": "ok"}

@app.get("/metrics", tags=["Monitoring"])
async def metrics() -> Response:
    """Expose Prometheus metrics for monitoring."""
    return Response(content=get_metrics(), media_type="text/plain; charset=utf-8")


@app.post("/chat", tags=["Chat"])
async def send_chat_message(
    chat_request: ChatRequest,
    ai_interface: Annotated[AIInterface, Depends(get_ai_interface)],
) -> ChatResponse:
    """Forward prompts to the configured ai_chat_api interface."""
    try:
        response = ai_interface.generate_response(
            user_input=chat_request.user_input,
            system_prompt=chat_request.system_prompt,
            response_schema=chat_request.response_schema,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI response could not be parsed: {exc}",
        ) from exc

    return ChatResponse(response=response)
