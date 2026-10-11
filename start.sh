#!/bin/bash
set -e

# If config.toml is missing, generate one from config.example.toml
if [ ! -f "config.toml" ] && [ -f "config.example.toml" ]; then
    echo "Creating config.toml from template..."
    cp config.example.toml config.toml
fi

# Write YOUTUBE_TOKEN_JSON from environment if provided
if [ -n "$YOUTUBE_TOKEN_JSON" ]; then
    echo "Writing youtube_token.json from environment variable..."
    echo "$YOUTUBE_TOKEN_JSON" > youtube_token.json
fi

# Inject any cloud environment variables into config.toml
python -c '
import os, toml
if os.path.exists("config.toml"):
    try:
        cfg = toml.load("config.toml")
        cfg.setdefault("app", {})["llm_provider"] = "gemini"
        cfg.setdefault("app", {})["gemini_model_name"] = "gemini-2.5-flash"
        if os.environ.get("GEMINI_API_KEY"):
            cfg.setdefault("app", {})["gemini_api_key"] = os.environ["GEMINI_API_KEY"]
            cfg["app"]["llm_provider"] = "gemini"
            cfg["app"]["gemini_model_name"] = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.5-flash")
        if os.environ.get("PEXELS_API_KEY"):
            cfg.setdefault("app", {})["pexels_api_keys"] = [os.environ["PEXELS_API_KEY"]]
        if os.environ.get("TELEGRAM_BOT_TOKEN"):
            cfg.setdefault("telegram", {})["bot_token"] = os.environ["TELEGRAM_BOT_TOKEN"]
        if os.environ.get("TELEGRAM_CHAT_ID"):
            cfg.setdefault("telegram", {})["chat_id"] = os.environ["TELEGRAM_CHAT_ID"]
        if os.environ.get("SECRET_PIN"):
            cfg.setdefault("telegram", {})["secret_pin"] = os.environ["SECRET_PIN"]
        if os.environ.get("YOUTUBE_CHANNEL_ID"):
            cfg.setdefault("app", {})["youtube_channel_id"] = os.environ["YOUTUBE_CHANNEL_ID"]
        with open("config.toml", "w") as f:
            toml.dump(cfg, f)
        print("Configuration updated from environment variables.")
    except Exception as e:
        print(f"Config injection warning: {e}")
'

echo "🚀 Starting VIP Telegram Controller Bot in background..."
python telegram_bot.py &

echo "🌐 Starting FastAPI Server with /health check on port ${PORT:-8080}..."
exec uvicorn app.asgi:app --host 0.0.0.0 --port ${PORT:-8080}
