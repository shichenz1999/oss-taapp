# HW3: Smart Chat Bot
integrate chat client and ai chat (for now).

## start up
### integrate with Discord
1. Create a bot in a discord app. Add it to a channel. 
2. Open the permisson: "Message Content Intent" for the bot in discord app config.
3. Copy the bot token and channel id to .env.

### Running command
```cmd
uv sync --all-packages --extra dev
.venv\Scripts\Activate.ps1
uvicorn src.smart_chat_bot.src.smart_chat_bot.main:app
```