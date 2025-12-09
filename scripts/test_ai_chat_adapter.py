"""Minimal manual check for ai_chat_adapter with a simple JSON schema."""

import ai_chat_adapter
import ai_chat_api

SCHEMA = {
    "type": "object",
    "properties": {"message": {"type": "string"}},
    "required": ["message"],
    "additionalProperties": False,
}


def main() -> None:
    ai_chat_adapter.register(base_url="http://127.0.0.1:8000")
    interface = ai_chat_api.get_ai_interface()
    result = interface.generate_response(
        user_input="what should you return?",
        response_schema=SCHEMA,
    )
    print(result)


if __name__ == "__main__":
    main()
