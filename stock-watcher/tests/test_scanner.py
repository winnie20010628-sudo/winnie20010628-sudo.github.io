from __future__ import annotations

import asyncio

from app.scanner import ScanResult, scan_target
from app.storage import WatchTarget


SAMPLE_BUYABLE = """
<html><head><title>限量特別色波鞋</title></head>
<body>
  <h1>限量特別色波鞋</h1>
  <p>現貨發售中，立即購買</p>
  <a href="/cart/add/123">加入購物車</a>
</body></html>
"""

SAMPLE_SOLD_OUT = """
<html><head><title>限量特別色波鞋</title></head>
<body>
  <h1>限量特別色波鞋</h1>
  <p>售罄 Sold Out</p>
</body></html>
"""


def test_scan_buyable(monkeypatch):
    async def fake_fetch(_url: str) -> str:
        return SAMPLE_BUYABLE

    monkeypatch.setattr("app.scanner.fetch_html", fake_fetch)
    target = WatchTarget(
        name="demo",
        url="https://shop.example.com/p/1",
        keywords=["特別色", "限量"],
    )
    result = asyncio.run(scan_target(target))
    assert result.status == "buyable"
    assert "cart" in result.purchase_url
    assert "特別色" in result.matched_keywords or "限量" in result.matched_keywords


def test_scan_sold_out(monkeypatch):
    async def fake_fetch(_url: str) -> str:
        return SAMPLE_SOLD_OUT

    monkeypatch.setattr("app.scanner.fetch_html", fake_fetch)
    target = WatchTarget(
        name="demo",
        url="https://shop.example.com/p/1",
        keywords=["特別色"],
    )
    result = asyncio.run(scan_target(target))
    assert result.status == "unavailable"


def test_scan_no_keyword(monkeypatch):
    async def fake_fetch(_url: str) -> str:
        return SAMPLE_BUYABLE

    monkeypatch.setattr("app.scanner.fetch_html", fake_fetch)
    target = WatchTarget(
        name="demo",
        url="https://shop.example.com/p/1",
        keywords=["完全唔存在嘅字"],
    )
    result = asyncio.run(scan_target(target))
    assert result.status == "no_match"


def test_fingerprint_stable():
    a = ScanResult(status="buyable", message="x", product_title="t", purchase_url="u", matched_keywords=["a"])
    b = ScanResult(status="buyable", message="x", product_title="t", purchase_url="u", matched_keywords=["a"])
    assert a.fingerprint == b.fingerprint
