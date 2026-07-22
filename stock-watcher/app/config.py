from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / "watchlist.json"
SETTINGS_FILE = DATA_DIR / "settings.json"


class Settings(BaseModel):
    whatsapp_phone: str = ""
    whatsapp_api_key: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = ""
    twilio_whatsapp_to: str = ""
    check_interval_seconds: int = Field(default=60, ge=15, le=3600)
    request_timeout_seconds: float = 25.0
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )


def _load_dotenv_fallback() -> dict[str, str]:
    """Optional .env support for advanced users."""
    env_path = BASE_DIR / ".env"
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw = line.split("=", 1)
        values[key.strip().lower()] = raw.strip().strip('"').strip("'")
    return values


def load_settings() -> Settings:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    env = _load_dotenv_fallback()
    mapping = {
        "whatsapp_phone": "whatsapp_phone",
        "whatsapp_api_key": "whatsapp_api_key",
        "twilio_account_sid": "twilio_account_sid",
        "twilio_auth_token": "twilio_auth_token",
        "twilio_whatsapp_from": "twilio_whatsapp_from",
        "twilio_whatsapp_to": "twilio_whatsapp_to",
        "check_interval_seconds": "check_interval_seconds",
    }
    for env_key, field in mapping.items():
        if env_key in env and env[env_key]:
            data[field] = env[env_key]

    if SETTINGS_FILE.exists():
        file_data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        data.update(file_data)

    if "check_interval_seconds" in data:
        data["check_interval_seconds"] = int(data["check_interval_seconds"])
    return Settings.model_validate(data)


def save_settings(settings: Settings) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        settings.model_dump_json(indent=2),
        encoding="utf-8",
    )


# Backward-compatible module attribute used by scanner/notifier
settings = load_settings()


def refresh_settings() -> Settings:
    global settings
    settings = load_settings()
    return settings


DATA_DIR.mkdir(parents=True, exist_ok=True)
