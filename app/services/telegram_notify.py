"""
Telegram Notification & Remote Controller Service
Sends real-time video generation updates, analytics summaries, and final MP4 videos to Telegram.
"""
import os
from pathlib import Path
from typing import Optional
import requests
from loguru import logger
from app.config import config


def get_telegram_credentials() -> tuple[str, str]:
    """Retrieve bot token and chat id from config or environment."""
    cfg_telegram = getattr(config, "telegram", None)
    if cfg_telegram is None and hasattr(config, "_cfg"):
        cfg_telegram = config._cfg.get("telegram", {})
    if not isinstance(cfg_telegram, dict):
        cfg_telegram = {}

    bot_token = (
        cfg_telegram.get("bot_token", "")
        or config.app.get("telegram_bot_token", "")
        or os.getenv("TELEGRAM_BOT_TOKEN", "")
    ).strip()

    chat_id = (
        cfg_telegram.get("chat_id", "")
        or config.app.get("telegram_chat_id", "")
        or os.getenv("TELEGRAM_CHAT_ID", "")
    ).strip()

    return bot_token, chat_id


def send_telegram_message(
    text: str,
    chat_id: Optional[str] = None,
    bot_token: Optional[str] = None,
    parse_mode: str = "HTML"
) -> bool:
    """Send text message via Telegram Bot API."""
    token, default_chat = get_telegram_credentials()
    final_token = bot_token or token
    final_chat = chat_id or default_chat

    if not final_token or not final_chat:
        logger.warning("Telegram credentials not configured. Skipping notification.")
        return False

    url = f"https://api.telegram.org/bot{final_token}/sendMessage"
    payload = {
        "chat_id": final_chat,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            logger.info("Telegram message sent successfully.")
            return True
        elif resp.status_code == 400 and parse_mode:
            logger.warning(f"Telegram parse error {resp.text}, retrying as plain text...")
            payload.pop("parse_mode", None)
            retry_resp = requests.post(url, json=payload, timeout=15)
            if retry_resp.status_code == 200:
                logger.info("Telegram message sent successfully as plain text fallback.")
                return True
        logger.error(f"Telegram error {resp.status_code}: {resp.text}")
        return False
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False


def send_telegram_video(
    video_path: str,
    caption: str = "",
    chat_id: Optional[str] = None,
    bot_token: Optional[str] = None
) -> bool:
    """Upload and send video file to Telegram."""
    token, default_chat = get_telegram_credentials()
    final_token = bot_token or token
    final_chat = chat_id or default_chat

    if not final_token or not final_chat:
        logger.warning("Telegram credentials not configured. Skipping video upload.")
        return False

    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return False

    url = f"https://api.telegram.org/bot{final_token}/sendVideo"
    data = {
        "chat_id": final_chat,
        "caption": caption[:1024],
        "parse_mode": "HTML",
        "supports_streaming": True
    }

    try:
        with open(video_path, "rb") as video_file:
            files = {"video": video_file}
            logger.info(f"Uploading video to Telegram: {video_path}...")
            resp = requests.post(url, data=data, files=files, timeout=120)
            if resp.status_code == 200:
                logger.success("Video sent to Telegram successfully!")
                return True
            else:
                logger.error(f"Telegram video upload failed {resp.status_code}: {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Failed to upload video to Telegram: {e}")
        return False


def notify_status(stage: str, title: str, details: str = ""):
    """Helper for formatted stage notification."""
    icons = {
        "start": "🚀",
        "analysis": "📊",
        "script": "✍️",
        "render": "🎬",
        "success": "🎉",
        "error": "⚠️"
    }
    icon = icons.get(stage.lower(), "🔔")
    msg = f"<b>{icon} MoneyPrinterTurbo: {title}</b>\n\n{details}"
    return send_telegram_message(msg)


def notify_alert(
    title: str,
    what_happened: str,
    technical_error: str = "",
    action_taken: str = "",
    severity: str = "ERROR"
) -> bool:
    """
    Direct Real-Time Telegram Alert for Render/Application issues.
    Delivers instant diagnostic report to Jayant Regar.
    """
    import html
    from datetime import datetime, timedelta, timezone

    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist_tz).strftime("%d-%m-%Y %I:%M:%S %p IST")

    severity_icons = {
        "INFO": "🟢",
        "WARNING": "⚠️",
        "ERROR": "🚨",
        "CRITICAL": "🔥"
    }
    icon = severity_icons.get(severity.upper(), "🚨")

    lines = [
        "╔═══════════════════════════════════╗",
        f"║   {icon} <b>RENDER SENTINEL: {severity.upper()}</b>",
        "╚═══════════════════════════════════╝",
        "",
        f"🕒 <b>Waqt:</b> <code>{now_ist}</code>",
        f"📌 <b>Component:</b> <b>{html.escape(str(title))}</b>",
        f"🔍 <b>Kya Hua:</b> {html.escape(str(what_happened))}"
    ]

    if action_taken:
        lines.append(f"🛠️ <b>System Action:</b> {html.escape(str(action_taken))}")

    if technical_error:
        clean_err = html.escape(str(technical_error)[-700:].strip())
        lines.append(f"\n📋 <b>Technical Error Log:</b>\n<pre>{clean_err}</pre>")

    lines.append("\n<i>MoneyPrinterTurbo Sentinel is actively monitoring Render 24/7.</i>")

    full_msg = "\n".join(lines)
    return send_telegram_message(full_msg)


_last_alert_times = {}


def install_telegram_error_sink():
    """Install global Loguru sink to catch ERROR/CRITICAL logs and alert Telegram."""
    import time

    def _telegram_sink(message):
        record = message.record
        level_no = record["level"].no
        if level_no < 40:
            return

        msg_text = record["message"]
        # Skip internal telegram errors or logs to prevent recursion loops
        if "telegram" in msg_text.lower() or "api.telegram.org" in msg_text.lower():
            return

        # Throttle: max 1 alert per error message signature every 120s
        key = msg_text[:60]
        now = time.time()
        last_t = _last_alert_times.get(key, 0)
        if now - last_t < 120:
            return
        _last_alert_times[key] = now

        loc = f"{record['file'].name}:{record['line']}"
        notify_alert(
            title=f"Error in {loc}",
            what_happened=f"Render application me error log hua:\n{msg_text[:200]}",
            technical_error=msg_text,
            action_taken="Recorded in server.log & Sentinel dispatched alert",
            severity="ERROR" if level_no < 50 else "CRITICAL"
        )

    try:
        logger.add(_telegram_sink, level="ERROR")
        logger.info("Telegram Error Alert Sentinel Sink successfully installed.")
    except Exception as e:
        logger.warning(f"Could not install telegram error sink: {e}")

