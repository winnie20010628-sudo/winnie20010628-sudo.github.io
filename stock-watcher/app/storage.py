from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from .config import DATA_FILE


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


DEFAULT_BUYABLE_KEYWORDS = [
    "加入購物車",
    "立即購買",
    "立即訂購",
    "有貨",
    "現貨",
    "Buy Now",
    "Add to cart",
    "Add to Bag",
    "In stock",
    "Purchase",
]

DEFAULT_SOLD_OUT_KEYWORDS = [
    "售罄",
    "缺貨",
    "暫時缺貨",
    "已售完",
    "Sold Out",
    "Out of stock",
    "Unavailable",
    "Notify me",
    "到貨通知",
]


class WatchTarget(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:10])
    name: str = ""
    url: str
    keywords: list[str] = Field(default_factory=list)
    buyable_keywords: list[str] = Field(default_factory=lambda: list(DEFAULT_BUYABLE_KEYWORDS))
    sold_out_keywords: list[str] = Field(default_factory=lambda: list(DEFAULT_SOLD_OUT_KEYWORDS))
    enabled: bool = True
    last_checked_at: str | None = None
    last_status: str = "pending"  # pending | buyable | unavailable | no_match | error
    last_message: str = ""
    last_notified_fingerprint: str | None = None
    created_at: str = Field(default_factory=utc_now)


class AppState(BaseModel):
    targets: list[WatchTarget] = Field(default_factory=list)
    recent_events: list[dict[str, Any]] = Field(default_factory=list)


_lock = threading.RLock()


def _default_state() -> AppState:
    return AppState()


def load_state() -> AppState:
    with _lock:
        if not DATA_FILE.exists():
            state = _default_state()
            save_state(state)
            return state
        raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return AppState.model_validate(raw)


def save_state(state: AppState) -> None:
    with _lock:
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(
            state.model_dump_json(indent=2),
            encoding="utf-8",
        )


def list_targets() -> list[WatchTarget]:
    return load_state().targets


def get_target(target_id: str) -> WatchTarget | None:
    for target in load_state().targets:
        if target.id == target_id:
            return target
    return None


def add_target(payload: dict[str, Any]) -> WatchTarget:
    state = load_state()
    keywords = _split_keywords(payload.get("keywords", ""))
    buyable = _split_keywords(payload.get("buyable_keywords", ""))
    sold_out = _split_keywords(payload.get("sold_out_keywords", ""))

    target = WatchTarget(
        name=(payload.get("name") or "").strip() or _hostname(payload["url"]),
        url=str(payload["url"]).strip(),
        keywords=keywords,
        buyable_keywords=buyable or list(DEFAULT_BUYABLE_KEYWORDS),
        sold_out_keywords=sold_out or list(DEFAULT_SOLD_OUT_KEYWORDS),
        enabled=bool(payload.get("enabled", True)),
    )
    state.targets.append(target)
    save_state(state)
    return target


def update_target(target_id: str, payload: dict[str, Any]) -> WatchTarget | None:
    state = load_state()
    for idx, target in enumerate(state.targets):
        if target.id != target_id:
            continue
        data = target.model_dump()
        if "name" in payload:
            data["name"] = (payload.get("name") or "").strip() or target.name
        if "url" in payload and payload["url"]:
            data["url"] = str(payload["url"]).strip()
        if "keywords" in payload:
            data["keywords"] = _split_keywords(payload.get("keywords", ""))
        if "buyable_keywords" in payload:
            data["buyable_keywords"] = (
                _split_keywords(payload.get("buyable_keywords", ""))
                or target.buyable_keywords
            )
        if "sold_out_keywords" in payload:
            data["sold_out_keywords"] = (
                _split_keywords(payload.get("sold_out_keywords", ""))
                or target.sold_out_keywords
            )
        if "enabled" in payload:
            data["enabled"] = bool(payload["enabled"])
        updated = WatchTarget.model_validate(data)
        state.targets[idx] = updated
        save_state(state)
        return updated
    return None


def delete_target(target_id: str) -> bool:
    state = load_state()
    before = len(state.targets)
    state.targets = [t for t in state.targets if t.id != target_id]
    if len(state.targets) == before:
        return False
    save_state(state)
    return True


def patch_target_result(
    target_id: str,
    *,
    status: str,
    message: str,
    fingerprint: str | None = None,
    notified: bool = False,
) -> None:
    state = load_state()
    for idx, target in enumerate(state.targets):
        if target.id != target_id:
            continue
        data = target.model_dump()
        data["last_checked_at"] = utc_now()
        data["last_status"] = status
        data["last_message"] = message
        if notified and fingerprint:
            data["last_notified_fingerprint"] = fingerprint
        state.targets[idx] = WatchTarget.model_validate(data)
        event = {
            "at": utc_now(),
            "target_id": target_id,
            "name": target.name,
            "status": status,
            "message": message,
            "notified": notified,
            "url": target.url,
        }
        state.recent_events.insert(0, event)
        state.recent_events = state.recent_events[:80]
        save_state(state)
        return


def recent_events(limit: int = 30) -> list[dict[str, Any]]:
    return load_state().recent_events[:limit]


def _split_keywords(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value)
    parts: list[str] = []
    for chunk in text.replace("，", ",").replace("\n", ",").split(","):
        item = chunk.strip()
        if item:
            parts.append(item)
    return parts


def _hostname(url: str) -> str:
    try:
        from urllib.parse import urlparse

        host = urlparse(url).netloc
        return host or url[:40]
    except Exception:
        return url[:40]
