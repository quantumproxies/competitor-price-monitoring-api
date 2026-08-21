"""The same product across markets — with the currency kept, never averaged away.

Prices are quoted per country because they are not comparable across countries:
VAT is included in the EU and not in the US, and many retailers price by visitor
location. This prints them side by side and leaves the conversion to you.

    python3 geo_prices.py "sony wh-1000xm5" --countries us gb de it jp
"""
from __future__ import annotations

import argparse
import statistics
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from prices import collect

# VAT included in the shelf price, for context — not applied, just displayed.
VAT_NOTE = {"de": "19% VAT incl.", "it": "22% VAT incl.", "fr": "20% VAT incl.",
            "es": "21% VAT incl.", "gb": "20% VAT incl.", "nl": "21% VAT incl.",
            "us": "sales tax NOT incl.", "jp": "10% tax incl.", "ca": "tax NOT incl."}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--countries", nargs="+", default=["us", "gb", "de", "it", "jp"])
    ap.add_argument("--max", type=int, default=20)
    args = ap.parse_args()

    def market(country: str):
        try:
            rows = collect("google_shopping", query=args.query, country=country,
                           max_results=args.max)
        except RuntimeError as exc:
            return country, [], str(exc)
        return country, rows, None

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(market, args.countries))

    print(f"{args.query}\n")
    print(f"{'market':<8}{'offers':>8}{'low':>12}{'median':>12}{'cur':>6}  note")
    by_currency = defaultdict(list)

    for country, rows, error in results:
        if error:
            print(f"{country:<8} !! {error}")
            continue
        priced = [r for r in rows if r.get("price_value")]
        if not priced:
            print(f"{country:<8}{len(rows):>8}   no priced offers")
            continue
        values = sorted(r["price_value"] for r in priced)
        currencies = {r.get("currency") for r in priced if r.get("currency")}
        cur = next(iter(currencies)) if len(currencies) == 1 else "mixed"
        by_currency[cur].append((country, statistics.median(values)))
        print(f"{country:<8}{len(priced):>8}{values[0]:>12,.2f}"
              f"{statistics.median(values):>12,.2f}{cur:>6}  {VAT_NOTE.get(country, '')}")

    print("\nComparable only within a currency column. Convert with the rate for the day "
          "you collected, and remember the tax line above before concluding anyone is cheaper.")


if __name__ == "__main__":
    main()
