# 🤖 Discord Bot Configuration Subsystem (`config/bot/`)

This directory manages credentials, intents, and runtime settings for **The Great Kasutamaiza** Discord bot.

---

## 📁 File Manifest

| File | Purpose |
| --- | --- |
| [`__init__.py`](file:///home/professorseanex/yugioh-server/config/bot/__init__.py) | Configuration loader module (`load_bot_config()`, `BOT_CONFIG`) |
| [`config.example.json`](file:///home/professorseanex/yugioh-server/config/bot/config.example.json) | Example JSON override template for local testing |
| [`README.md`](file:///home/professorseanex/yugioh-server/config/bot/README.md) | Subsystem documentation (this file) |

---

## 🔑 Configuration Resolution Hierarchy

The bot resolves its configuration using the following priority:

1. **Environment Variables** (`.env` or OS environment):
   - `DISCORD_BOT_TOKEN`: The bot authentication token.
   - `DISCORD_GUILD_ID`: Target Discord server ID for instant slash command registration.
   - `DISCORD_COMMAND_PREFIX`: Fallback prefix for message commands (default: `!`).
   - `DISCORD_CLIENT_ID`: Application client ID for OAuth2 invite generation.
2. **Local JSON File** (`config/bot/config.json`):
   - If present, overrides values loaded from `.env`. Useful for running local staging instances without modifying global secrets.
3. **Defaults**:
   - `prefix`: `!`
   - `guild_id`: `None` (registers commands globally across Discord, which may take up to 1 hour to propagate).

---

## ⚙️ JSON Schema Reference (`config.json`)

```json
{
  "token": "YOUR_DISCORD_BOT_TOKEN_HERE",
  "guild_id": 1551494268575817778,
  "client_id": 1555176044536012880,
  "prefix": "!"
}
```

- **`token`** *(string)*: Secret bot token obtained from the [Discord Developer Portal](https://discord.com/developers/applications).
- **`guild_id`** *(integer)*: Server ID where slash commands are synchronized immediately upon boot.
- **`client_id`** *(integer)*: Application ID used for creating bot invite URLs.
- **`prefix`** *(string)*: Command prefix for non-slash fallback commands.

---

## 🚀 Usage in Python

```python
from config.bot import BOT_CONFIG, load_bot_config

# Access active credentials
token = BOT_CONFIG["token"]
guild_id = BOT_CONFIG["guild_id"]
db_path = BOT_CONFIG["db_path"]
```
