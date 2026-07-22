from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import settings
from .monitor import check_all, check_one
from .notifier import send_whatsapp
from .storage import (
    add_target,
    delete_target,
    get_target,
    list_targets,
    recent_events,
    update_target,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("stock_watcher")

BASE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE / "templates"))
scheduler = AsyncIOScheduler()


async def _scheduled_check() -> None:
    logger.info("Running scheduled check…")
    await check_all(only_enabled=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler.add_job(
        _scheduled_check,
        "interval",
        seconds=max(15, settings.check_interval_seconds),
        id="stock_check",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info(
        "Scheduler started (every %s seconds)", settings.check_interval_seconds
    )
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Stock Watcher", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")


def _whatsapp_ready() -> bool:
    if settings.twilio_account_sid and settings.twilio_auth_token:
        return bool(settings.twilio_whatsapp_from and settings.twilio_whatsapp_to)
    return bool(settings.whatsapp_phone and settings.whatsapp_api_key)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "targets": list_targets(),
            "events": recent_events(40),
            "interval": settings.check_interval_seconds,
            "whatsapp_ready": _whatsapp_ready(),
            "phone_masked": _mask_phone(settings.whatsapp_phone),
        },
    )


@app.post("/targets")
async def create_target(
    name: str = Form(""),
    url: str = Form(...),
    keywords: str = Form(""),
    buyable_keywords: str = Form(""),
    sold_out_keywords: str = Form(""),
) -> RedirectResponse:
    if not url.strip().startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="網址必須以 http:// 或 https:// 開頭")
    add_target(
        {
            "name": name,
            "url": url,
            "keywords": keywords,
            "buyable_keywords": buyable_keywords,
            "sold_out_keywords": sold_out_keywords,
            "enabled": True,
        }
    )
    return RedirectResponse("/", status_code=303)


@app.post("/targets/{target_id}/toggle")
async def toggle_target(target_id: str) -> RedirectResponse:
    target = get_target(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="找不到監控項目")
    update_target(target_id, {"enabled": not target.enabled})
    return RedirectResponse("/", status_code=303)


@app.post("/targets/{target_id}/delete")
async def remove_target(target_id: str) -> RedirectResponse:
    if not delete_target(target_id):
        raise HTTPException(status_code=404, detail="找不到監控項目")
    return RedirectResponse("/", status_code=303)


@app.post("/targets/{target_id}/check")
async def check_target_now(target_id: str) -> RedirectResponse:
    target = get_target(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="找不到監控項目")
    await check_one(target, force_notify=False)
    return RedirectResponse("/", status_code=303)


@app.post("/check-now")
async def check_now() -> RedirectResponse:
    await check_all(only_enabled=True)
    return RedirectResponse("/", status_code=303)


@app.post("/api/test-whatsapp")
async def test_whatsapp() -> JSONResponse:
    ok, detail = await send_whatsapp(
        "✅ Stock Watcher 測試訊息\n如果你收到呢條，WhatsApp 通知已設定成功。"
    )
    return JSONResponse({"ok": ok, "detail": detail})


@app.get("/api/targets")
async def api_targets() -> list[dict[str, Any]]:
    return [t.model_dump() for t in list_targets()]


@app.get("/api/events")
async def api_events() -> list[dict[str, Any]]:
    return recent_events(50)


def _mask_phone(phone: str) -> str:
    digits = phone.replace(" ", "").replace("+", "")
    if len(digits) < 6:
        return phone or "未設定"
    return f"+{digits[:3]}****{digits[-2:]}"


def run() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )


if __name__ == "__main__":
    run()
