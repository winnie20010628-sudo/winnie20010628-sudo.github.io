from __future__ import annotations

import logging

from .notifier import notify_buyable
from .scanner import scan_target
from .storage import WatchTarget, list_targets, patch_target_result

logger = logging.getLogger(__name__)


async def check_one(target: WatchTarget, *, force_notify: bool = False) -> dict:
    result = await scan_target(target)
    notified = False
    notify_detail = ""

    if result.status == "buyable":
        should_notify = force_notify or (
            target.last_notified_fingerprint != result.fingerprint
        )
        if should_notify:
            ok, notify_detail = await notify_buyable(target, result)
            notified = ok
            if not ok:
                logger.warning("Notify failed for %s: %s", target.id, notify_detail)
        else:
            notify_detail = "狀態未變，略過重複通知"

    patch_target_result(
        target.id,
        status=result.status,
        message=result.message if not notify_detail else f"{result.message}｜{notify_detail}",
        fingerprint=result.fingerprint if notified else None,
        notified=notified,
    )

    return {
        "target_id": target.id,
        "name": target.name,
        "status": result.status,
        "message": result.message,
        "purchase_url": result.purchase_url,
        "product_title": result.product_title,
        "matched_keywords": result.matched_keywords,
        "notified": notified,
        "notify_detail": notify_detail,
    }


async def check_all(*, only_enabled: bool = True) -> list[dict]:
    results = []
    targets = list_targets()
    for target in targets:
        if only_enabled and not target.enabled:
            continue
        try:
            results.append(await check_one(target))
        except Exception as exc:
            logger.exception("Check failed for %s", target.id)
            patch_target_result(
                target.id,
                status="error",
                message=f"檢查失敗：{exc}",
            )
            results.append(
                {
                    "target_id": target.id,
                    "name": target.name,
                    "status": "error",
                    "message": str(exc),
                    "notified": False,
                }
            )
    return results
