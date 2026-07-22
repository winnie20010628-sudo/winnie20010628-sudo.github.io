from __future__ import annotations

import logging
from urllib.parse import quote

import httpx

from .config import settings
from .scanner import ScanResult
from .storage import WatchTarget

logger = logging.getLogger(__name__)


def _format_message(target: WatchTarget, result: ScanResult) -> str:
    keywords = ", ".join(result.matched_keywords) if result.matched_keywords else "—"
    title = result.product_title or target.name
    return (
        "🛒 可購買貨品通知\n"
        f"商品：{title}\n"
        f"監控：{target.name}\n"
        f"關鍵字：{keywords}\n"
        f"購買連結：{result.purchase_url}"
    )


async def send_whatsapp(message: str) -> tuple[bool, str]:
    if _twilio_configured():
        return await _send_twilio(message)
    if settings.whatsapp_phone and settings.whatsapp_api_key:
        return await _send_callmebot(message)
    return False, "尚未設定 WhatsApp（請在 .env 填寫 WHATSAPP_PHONE 與 WHATSAPP_API_KEY）"


def _twilio_configured() -> bool:
    return bool(
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_whatsapp_from
        and settings.twilio_whatsapp_to
    )


async def _send_callmebot(message: str) -> tuple[bool, str]:
    phone = settings.whatsapp_phone.lstrip("+").replace(" ", "")
    url = (
        "https://api.callmebot.com/whatsapp.php"
        f"?phone={quote(phone)}"
        f"&text={quote(message)}"
        f"&apikey={quote(settings.whatsapp_api_key)}"
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            body = response.text.strip()
            if response.status_code == 200 and "error" not in body.lower():
                return True, "已透過 CallMeBot 發送 WhatsApp"
            return False, f"CallMeBot 失敗（{response.status_code}）：{body[:200]}"
    except Exception as exc:
        logger.exception("CallMeBot send failed")
        return False, f"CallMeBot 例外：{exc}"


async def _send_twilio(message: str) -> tuple[bool, str]:
    url = (
        f"https://api.twilio.com/2010-04-01/Accounts/"
        f"{settings.twilio_account_sid}/Messages.json"
    )
    data = {
        "From": settings.twilio_whatsapp_from,
        "To": settings.twilio_whatsapp_to,
        "Body": message,
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                data=data,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            )
            if response.status_code in (200, 201):
                return True, "已透過 Twilio 發送 WhatsApp"
            return False, f"Twilio 失敗（{response.status_code}）：{response.text[:200]}"
    except Exception as exc:
        logger.exception("Twilio send failed")
        return False, f"Twilio 例外：{exc}"


async def notify_buyable(target: WatchTarget, result: ScanResult) -> tuple[bool, str]:
    message = _format_message(target, result)
    return await send_whatsapp(message)
