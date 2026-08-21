"""Four price sources behind one function.

Every quote carries where it came from, which seller it belongs to, its currency
and the country it was collected from. Without those four fields a price sheet is
a pile of numbers that cannot be compared.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests

BASE = "https://api.quanticdata.io/v1"
_s = requests.Session()


def _h() -> dict[str, str]:
    key = os.environ.get("QUANTICDATA_API_KEY")
    if not key:
        raise SystemExit("set QUANTICDATA_API_KEY — https://app.quanticdata.io/register")
    return {"Authorization": f"Bearer {key}"}


def _payload(r: requests.Response, what: str) -> dict:
    data = r.json()
    if data.get("type") == "error" or not r.ok:
        raise RuntimeError(f"{what} ({r.status_code}): {data.get('message')}")
    return data.get("payload", {})


def collect(slug: str, **input_: Any) -> list[dict]:
    payload = {k: v for k, v in input_.items() if v not in (None, "", [])}
    run = _payload(_s.post(f"{BASE}/scraper/collectors/{slug}/run", json=payload,
                           headers=_h(), timeout=300), slug)
    while run.get("status") in ("queued", "running"):
        time.sleep(3)
        run = _payload(_s.get(f"{BASE}/scraper/collectors/runs/{run['run_id']}",
                              headers=_h(), timeout=60), "run status")
    return run.get("results") or []


def scrape(url: str, country: str | None = None) -> dict:
    return _payload(_s.post(f"{BASE}/scrape", json={
        "url": url, "country": country,
        "extract": {
            "price": '[itemprop=price], .price, [data-price], .product-price',
            "availability": '[itemprop=availability], .stock, .availability',
            "title": "h1",
        },
    }, headers=_h(), timeout=180), "scrape")


def _quote(source: str, seller: str | None, price, currency: str | None,
           country: str, extra: dict | None = None) -> dict:
    return {"source": source, "seller": seller, "price_value": price,
            "currency": currency, "country": country, **(extra or {})}


def quotes(product: dict, country: str = "us", lang: str = "en") -> list[dict]:
    """Every price we can find for one product, from every source it supports."""
    out: list[dict] = []

    if product.get("query"):
        for row in collect("google_shopping", query=product["query"],
                           country=country, lang=lang, max_results=20):
            out.append(_quote("google_shopping", row.get("seller"), row.get("price_value"),
                              row.get("currency"), country,
                              {"title": row.get("title"), "link": row.get("link"),
                               "product_id": row.get("product_id"),
                               "rating": row.get("rating"), "condition": row.get("condition")}))

        # product_offers needs a product id; reuse the best one Shopping just gave us.
        product_id = product.get("product_id") or next(
            (q.get("product_id") for q in out if q.get("product_id")), None)
        if product_id:
            for row in collect("product_offers", product_id=product_id, query=product["query"],
                               country=country, lang=lang, max_results=20):
                out.append(_quote("product_offers", row.get("seller"), row.get("price_value"),
                                  row.get("currency"), country,
                                  {"title": row.get("product_title"),
                                   "link": row.get("link"),
                                   "total_price": row.get("total_price")}))

    if product.get("asin"):
        for row in collect("amazon_product", asins=[product["asin"]],
                           country=country, max_results=1):
            out.append(_quote("amazon", row.get("seller") or "Amazon", row.get("price_value"),
                              None, country,
                              {"title": row.get("title"), "link": row.get("url"),
                               "availability": row.get("availability"),
                               "list_price": row.get("list_price")}))

    for url in product.get("urls") or []:
        try:
            payload = scrape(url, country)
        except RuntimeError as exc:
            out.append(_quote("own_page", url, None, None, country, {"error": str(exc)}))
            continue
        data = payload.get("data") or {}
        out.append(_quote("own_page", url, parse_price(data.get("price")), None, country,
                          {"title": data.get("title"), "link": url,
                           "availability": data.get("availability"),
                           "raw_price": data.get("price")}))

    return out


def parse_price(text: Any) -> float | None:
    """'€1.299,00' / '$1,299.00' -> 1299.0. Returns None rather than guessing."""
    if isinstance(text, (int, float)):
        return float(text)
    if not isinstance(text, str):
        return None
    digits = "".join(c for c in text if c.isdigit() or c in ".,")
    if not digits:
        return None
    # Whichever separator comes last is the decimal one.
    if "," in digits and "." in digits:
        decimal = "," if digits.rfind(",") > digits.rfind(".") else "."
        thousands = "." if decimal == "," else ","
        digits = digits.replace(thousands, "").replace(decimal, ".")
    elif "," in digits:
        digits = digits.replace(",", "." if len(digits.split(",")[-1]) == 2 else "")
    try:
        return float(digits)
    except ValueError:
        return None
