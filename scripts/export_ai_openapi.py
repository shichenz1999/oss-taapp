"""Export the OpenAPI spec (JSON) for the AI Chat FastAPI service.

Writes the spec to docs/ai_chat_service_openapi.json so we can
generate a typed client via openapi-python-client.

Usage (from repo root):
    python -m scripts.export_ai_openapi
"""

from pathlib import Path
import json
import os

from fastapi.openapi.utils import get_openapi

# Provide minimal dummy settings so importing the app does not fail
os.environ.setdefault("CLAUDE_API_KEY", "dummy")
os.environ.setdefault("OAUTH_CLIENT_ID", "dummy")
os.environ.setdefault("OAUTH_CLIENT_SECRET", "dummy")
os.environ.setdefault("SESSION_SECRET_KEY", "dummy")

try:
    # Import the FastAPI app instance
    from ai_chat_service import app
except Exception as exc:
    raise SystemExit(f"Failed to import FastAPI app: {exc}") from exc


def main() -> None:
    spec = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description=app.description,
    )

    out_path = Path(__file__).resolve().parents[1] / "docs" / "ai_chat_service_openapi.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote OpenAPI JSON to: {out_path}")


if __name__ == "__main__":
    main()
