"""Scarica in cache azioni (`shares_full`) e date report per i ticker risolti. Ripartibile."""

from __future__ import annotations

import pandas as pd

from . import yf_cache


def usable_symbols(resolution: pd.DataFrame) -> list[str]:
    ok = resolution[resolution["symbol"].notna() & (resolution["verified"].isna() | resolution["verified"].map(lambda v: v is True or v == 1))]
    return sorted(set(ok["symbol"]))


def enrich(symbols: list[str], progress=None) -> dict:
    stats = {"shares_ok": 0, "reports_ok": 0, "n": len(symbols)}
    for i, sym in enumerate(symbols, start=1):
        if yf_cache.shares_full(sym) is not None:
            stats["shares_ok"] += 1
        if yf_cache.earnings_dates(sym) is not None:
            stats["reports_ok"] += 1
        if progress and i % 50 == 0:
            progress(i, stats)
    return stats
