# Competitor price monitoring — one price sheet from four different sources

Prices live in four different shapes, and a monitoring system that only reads one of them has
blind spots:

| Source | Collector / endpoint | Good for |
|---|---|---|
| Google Shopping | [`google_shopping`](https://quanticdata.io/collectors/google-shopping-api/) | who sells it and at what price, across retailers |
| Offers for one product | [`product_offers`](https://quanticdata.io/collectors/price-comparison-api/) | every seller for a known product id, plus typical prices |
| Amazon | [`amazon_search`](https://quanticdata.io/collectors/amazon-scraper-api/) / [`amazon_product`](https://quanticdata.io/collectors/amazon-product-api/) | the marketplace that sets the reference price |
| The competitor's own page | [`POST /v1/scrape`](https://quanticdata.io/web-scraping-api/) | the truth, including their promo banner |

This repo pulls all four into one CSV history and reports what moved, in the currency and
country you care about.

[Competitor price monitoring](https://quanticdata.io/competitor-price-monitoring/) ·
[QuanticData](https://quanticdata.io)

```bash
pip install requests
export QUANTICDATA_API_KEY=qd_live_your_key_here

python3 sheet.py products.json --country us --out prices.csv
python3 movers.py prices.csv --since 7        # what changed in the last week
python3 geo_prices.py "sony wh-1000xm5" --countries us gb de it jp
```

## Files

| File | What it does |
|---|---|
| [`prices.py`](prices.py) | the four sources behind one `quotes(product)` function |
| [`sheet.py`](sheet.py) | append today's prices for a product list to a CSV history |
| [`movers.py`](movers.py) | read the history, report changes, undercuts and new sellers |
| [`geo_prices.py`](geo_prices.py) | the same product across markets — currency, tax and availability differ |
| [`products.json`](products.json) | the input format, with one worked example |

## The input

```json
[
  { "name": "Sony WH-1000XM5",
    "query": "sony wh-1000xm5",
    "asin": "B09XS7JWHH",
    "urls": ["https://competitor.example/products/sony-wh-1000xm5"] }
]
```

Everything except `name` is optional — give it what you have, and each source that can answer,
answers.

## Two things that make price data wrong

**Currency and tax.** A German price includes 19% VAT; a US price does not include sales tax.
Comparing `price_value` across `country` without normalising is the single most common error in
price monitoring, and it makes every European competitor look expensive. `geo_prices.py` prints
the currency next to every figure and refuses to average across them.

**Geo-served prices.** Many retailers price by visitor location. Scraping their page from one
country tells you what customers *in that country* pay, and nothing about the rest. Pass
`country` on every call and store it with the row — `sheet.py` does.

## Cost

Google Shopping $0.001/listing, product offers $0.002/offer, Amazon $0.001–$0.003/product,
a competitor page $0.0002. Monitoring 50 products daily across three sources is a few dollars a
month, and failures are not billed.

## Related

- [Competitor price monitoring](https://quanticdata.io/competitor-price-monitoring/) · [Price comparison API](https://quanticdata.io/collectors/price-comparison-api/) · [Google Shopping API](https://quanticdata.io/collectors/google-shopping-api/)
- [How to price-monitor](https://quanticdata.io/blog/how-to-price-monitor/) · [How to price-watch on Amazon](https://quanticdata.io/blog/how-to-price-watch-on-amazon/)
- [Market research data](https://quanticdata.io/market-research-data/) · [All collectors](https://quanticdata.io/collectors/)

MIT licensed.
