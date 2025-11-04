import json
import sys
from pathlib import Path

# Ensure src paths are importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "claude_chat_service" / "src"))

from claude_chat_service.main import app  # type: ignore

schema = app.openapi()
out_dir = ROOT / "build"
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "claude_chat_service_openapi.json"
out_file.write_text(json.dumps(schema, indent=2), encoding="utf-8")
print(out_file)
