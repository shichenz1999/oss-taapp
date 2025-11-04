# AI Conversation Service

FastAPI wrapper around the Claude implementation.

## Install
```bash
uv pip install -e "src/ai_conversation_service[test]"
```

## Run
```bash
export ANTHROPIC_API_KEY="sk-..."
uvicorn ai_conversation_service:app --reload
```

## Test
```bash
pytest src/ai_conversation_service/tests
```
