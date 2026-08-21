"""Read the price history and say what actually changed.

Three questions, answered from the same CSV: which sellers moved, who is
undercutting whom today, and which sellers are new since the window started.

    python3 movers.py prices.csv --since 7 --threshold 2
"""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from datetime import date, timedelta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--since", type=int, default=7, help="window in days")
    ap.add_argument("--threshold", type=float, default=1.0, help="report moves above this %")
    args = ap.parse_args()

    cutoff = (date.today() - timedelta(days=args.since)).isoformat()

    # (product, source, seller) -> {date: price}
    series: dict[tuple, dict[str, float]] = defaultdict(dict)
    currency: dict[tuple, str] = {}
    with open(args.file, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if not row.get("price_value"):
                continue
            try:
                price = float(row["price_value"])
            except ValueError:
                continue
            key = (row["product"], row["source"], row.get("seller") or "?")
            series[key][row["date"]] = price
            currency[key] = row.get("currency") or ""

    print(f"changes over the last {args.since} days (>{args.threshold}%)\n")
    moves = []
    for key, points in series.items():
        dates = sorted(points)
        recent = [d for d in dates if d >= cutoff]
        if len(recent) < 2:
            continue
        first, last = points[recent[0]], points[recent[-1]]
        if not first:
            continue
        delta = 100 * (last - first) / first
        if abs(delta) >= args.threshold:
            moves.append((delta, key, first, last, recent[0], recent[-1]))

    for delta, (product, source, seller), first, last, d0, d1 in sorted(moves, key=lambda t: t[0]):
        arrow = "▲" if delta > 0 else "▼"
        print(f"{arrow} {delta:>6.1f}%  {product[:24]:<25}{seller[:20]:<21}"
              f"{first:>9.2f} → {last:<9.2f} {currency.get((product, source, seller), '')}"
              f"  ({d0}→{d1})")
    if not moves:
        print("  nothing moved")

    latest = defaultdict(list)
    for key, points in series.items():
        last_date = max(points)
        latest[key[0]].append((points[last_date], key[2], key[1]))

    print("\ncheapest seller right now")
    for product, offers in latest.items():
        offers.sort()
        best = offers[0]
        runner = offers[1] if len(offers) > 1 else None
        gap = f"  (next {runner[0]:.2f} at {runner[1]})" if runner else ""
        print(f"  {product[:28]:<30}{best[0]:>9.2f}  {best[1]}  [{best[2]}]{gap}")

    print("\nsellers first seen inside the window")
    for key, points in series.items():
        if min(points) >= cutoff and len(points) >= 1:
            print(f"  {key[0][:26]:<28}{key[2][:24]:<26}[{key[1]}]")


if __name__ == "__main__":
    main()
