"""Quick sanity-check for Claude conversation API."""

import ai_conversation_impl  # noqa: F401
from ai_conversation_api import get_client
from ai_conversation_impl import ClaudeClient, ClaudeSession

def main() -> None:
    client = get_client()
    print(f"client type: {type(client).__name__}")
    print(f"is ClaudeClient? {isinstance(client, ClaudeClient)}")

    print("\n--- Create sessions ---")
    session1 = client.create_session()
    print(f"session1 id: {session1.id}")

    print("\n--- Session.send round-trip ---")
    session = session1
    print("session1:")
    prompt1 = "Reply in a single sentence: Which planet is known as the Red Planet?"
    print("user:", prompt1)
    reply1 = session.send(prompt1)
    print("assistant:", reply1)

    print("\n--- Client.send with explicit session_id ---")
    print("session1:")
    prompt2 = "Answer in one short sentence: How many continents are there on Earth?"
    print("user:", prompt2)
    reply2 = client.send(prompt2, session_id=session.id)
    print("assistant:", reply2)

    print("\n--- Client.send with implicit new session ---")
    print("session2 (auto-created):")
    prompt3 = (
        "Respond with a single sentence: Name one programming language created by Guido van Rossum."
    )
    print("user:", prompt3)
    reply3 = client.send(prompt3)
    print("assistant:", reply3)

    print("\n--- Session history (session1) ---")
    for message in session.history:
        print(f"{message.role}: {message.content}")

    print("\n--- List sessions ---")
    sessions = list(client.list_sessions())
    for idx, sess in enumerate(sessions, start=1):
        print(f"session #{idx}: id={sess.id}, type={type(sess).__name__}")

    print("\n--- Delete all sessions and verify ---")
    all_sessions = list(client.list_sessions())
    for sess in all_sessions:
        print("deleting:", sess.id)
        print("deleted?", client.delete_session(sess.id))
    sessions = list(client.list_sessions())
    for idx, sess in enumerate(sessions, start=1):
        print(f"remaining session #{idx}: id={sess.id}, type={type(sess).__name__}")
    if not sessions:
        print("no remaining sessions")

if __name__ == "__main__":
    main()
