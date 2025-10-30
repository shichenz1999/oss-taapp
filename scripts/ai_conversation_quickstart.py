"""Minimal sanity check for the Claude conversation client."""

import ai_conversation_impl  # noqa: F401
from ai_conversation_api import get_client


def main() -> None:
    client = get_client()
    session = client.create_session()
    prompt = "Reply in a single sentence: what is open source software development?"
    print("user:", prompt)
    reply = session.send(prompt)
    print("assistant:", reply)


if __name__ == "__main__":
    main()
