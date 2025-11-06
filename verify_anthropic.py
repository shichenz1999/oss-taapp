# verify_anthropic.py
from anthropic import Anthropic
import os
import sys

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    sys.exit("ANTHROPIC_API_KEY is missing in environment variables.")

client = Anthropic(api_key=api_key)

try:
    client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1,
        messages=[{"role": "user", "content": "ping"}],
    )
    print("API key works.")
except Exception as exc:
    print(f"API call failed: {exc}")