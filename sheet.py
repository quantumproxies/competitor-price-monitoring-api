"""Append today's prices for a product list to a CSV history.

    python3 sheet.py products.json --country us --out prices.csv

The CSV is the database. One row per quote per day, with source, seller, currency
and country — everything needed to compare correctly later.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
from datetime import date

from prices import quotes

FIELDS = ["date", "product", "source", "seller", "price_value", "currency", "country",
          "title", "availability", "link"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("products", type=pathlib.Path)
    ap.add_argument("--country", default="us")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--out", default="prices.csv")
    args = ap.parse_args()

    products = json.loads(args.products.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    out = pathlib.Path(args.out)
    fresh = not out.exists()

    written = 0
    with out.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        if fresh:
            w.writeheader()

        for product in products:
            rows = quotes(product, country=args.country, lang=args.lang)
            priced = [r for r in rows if r.get("price_value")]
            for row in rows:
                w.writerow({"date": today, "product": product["name"], **row})
                written += 1

            if priced:
                cheapest = min(priced, key=lambda r: r["price_value"])
                print(f"{product['name']:<28} {len(priced):>3} quotes   "
                      f"low {cheapest['price_value']} at {cheapest.get('seller')}")
            else:
                print(f"{product['name']:<28}   no priced quotes")

    print(f"\n{written} rows appended to {out}")


if __name__ == "__main__":
    main()
