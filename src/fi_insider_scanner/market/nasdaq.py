"""Liste Nasdaq Nordic (Stoccolma Main Market e First North): ISIN -> simbolo, solo titoli attivi."""

from __future__ import annotations

import json
import time
import urllib.request

import pandas as pd

from .. import config

URL = "https://api.nasdaq.com/api/nordic/screener/shares?category={category}&tableonly=false&market=STO"
CATEGORIES = ("MAIN_MARKET", "FIRST_NORTH")


def _fetch(category: str) -> list[dict]:
    cache = config.CACHE_DIR / "nasdaq" / f"{category}.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    req = urllib.request.Request(URL.format(category=category), headers={"User-Agent": "fi-insider-scanner/0.1 (research)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read())
    rows = payload["data"]["instrumentListing"]["rows"]
    cache.write_text(json.dumps(rows), encoding="utf-8")
    time.sleep(1.0)
    return rows


def yahoo_symbol(nasdaq_symbol: str) -> str:
    return nasdaq_symbol.strip().replace(" ", "-") + ".ST"


def listings() -> pd.DataFrame:
    rows = []
    for cat in CATEGORIES:
        for r in _fetch(cat):
            if r.get("isin") and r.get("symbol"):
                rows.append({"isin": r["isin"], "symbol": r["symbol"], "yahoo": yahoo_symbol(r["symbol"]), "name": r.get("fullName"), "currency": r.get("currency"), "segment": cat})
    return pd.DataFrame(rows).drop_duplicates("isin")
