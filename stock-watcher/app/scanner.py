from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .config import load_settings
from .storage import WatchTarget


@dataclass
class ScanResult:
    status: str  # buyable | unavailable | no_match | error
    message: str
    product_title: str = ""
    purchase_url: str = ""
    matched_keywords: list[str] | None = None
    fingerprint: str = ""

    def __post_init__(self) -> None:
        if self.matched_keywords is None:
            self.matched_keywords = []
        if not self.fingerprint:
            raw = f"{self.status}|{self.purchase_url}|{self.product_title}|{','.join(self.matched_keywords)}"
            self.fingerprint = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _find_matches(text: str, keywords: list[str]) -> list[str]:
    lowered = text.lower()
    hits: list[str] = []
    for keyword in keywords:
        key = keyword.strip()
        if not key:
            continue
        if key.lower() in lowered:
            hits.append(key)
    return hits


def _pick_title(soup: BeautifulSoup, fallback: str) -> str:
    for selector in ("h1", "meta[property='og:title']", "title"):
        if selector.startswith("meta"):
            tag = soup.select_one(selector)
            if tag and tag.get("content"):
                return _normalize_text(tag["content"])
        else:
            tag = soup.select_one(selector)
            if tag:
                return _normalize_text(tag.get_text(" ", strip=True))
    return fallback


def _extract_purchase_url(soup: BeautifulSoup, page_url: str) -> str | None:
    """Prefer add-to-cart / checkout / buy links; fall back to canonical / page URL."""
    buy_patterns = [
        r"cart",
        r"checkout",
        r"buy",
        r"purchase",
        r"order",
        r"add[-_]?to",
        r"購物車",
        r"結帳",
        r"結賬",
        r"立即購買",
        r"立即訂購",
        r"下單",
    ]
    pattern = re.compile("|".join(buy_patterns), re.I)

    candidates: list[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        label = _normalize_text(a.get_text(" ", strip=True))
        combined = f"{href} {label}"
        if pattern.search(combined):
            candidates.append(urljoin(page_url, href))

    for form in soup.find_all("form", action=True):
        action = form.get("action", "")
        if pattern.search(action or ""):
            candidates.append(urljoin(page_url, action))

    # Absolute same-host links first
    page_host = urlparse(page_url).netloc
    for link in candidates:
        if urlparse(link).netloc == page_host:
            return link
    if candidates:
        return candidates[0]

    canonical = soup.select_one("link[rel='canonical']")
    if canonical and canonical.get("href"):
        return urljoin(page_url, canonical["href"])
    return page_url


def _visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    return _normalize_text(soup.get_text(" ", strip=True))


async def fetch_html(url: str) -> str:
    settings = load_settings()
    headers = {
        "User-Agent": settings.user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-HK,zh-TW;q=0.9,zh;q=0.8,en;q=0.7",
    }
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=settings.request_timeout_seconds,
        headers=headers,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def scan_target(target: WatchTarget) -> ScanResult:
    try:
        html = await fetch_html(target.url)
    except Exception as exc:  # network / HTTP errors
        return ScanResult(
            status="error",
            message=f"無法讀取網頁：{exc}",
            purchase_url=target.url,
        )

    soup = BeautifulSoup(html, "lxml")
    text = _visible_text(soup)
    title = _pick_title(soup, target.name or target.url)

    keyword_hits = _find_matches(text, target.keywords)
    if target.keywords and not keyword_hits:
        return ScanResult(
            status="no_match",
            message="頁面未出現你設定的關鍵字",
            product_title=title,
            purchase_url=target.url,
            matched_keywords=[],
        )

    sold_out_hits = _find_matches(text, target.sold_out_keywords)
    buyable_hits = _find_matches(text, target.buyable_keywords)

    # Only notify when buyable signals exist and sold-out does not dominate.
    if buyable_hits and not sold_out_hits:
        purchase_url = _extract_purchase_url(soup, target.url) or target.url
        matched = keyword_hits or buyable_hits
        return ScanResult(
            status="buyable",
            message="偵測到可購買商品",
            product_title=title,
            purchase_url=purchase_url,
            matched_keywords=matched,
        )

    if sold_out_hits and not buyable_hits:
        return ScanResult(
            status="unavailable",
            message=f"目前不可購買（找到：{', '.join(sold_out_hits[:3])}）",
            product_title=title,
            purchase_url=target.url,
            matched_keywords=keyword_hits,
        )

    if buyable_hits and sold_out_hits:
        # Ambiguous page (e.g. related products). Prefer unavailable to avoid false alerts.
        return ScanResult(
            status="unavailable",
            message="同時出現可購買與售罄字樣，暫不通知以免誤報",
            product_title=title,
            purchase_url=target.url,
            matched_keywords=keyword_hits,
        )

    return ScanResult(
        status="unavailable",
        message="未找到可購買按鈕／字樣",
        product_title=title,
        purchase_url=target.url,
        matched_keywords=keyword_hits,
    )
