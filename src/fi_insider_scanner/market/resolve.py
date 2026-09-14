"""ISIN azionario -> ticker Yahoo `.ST`, sempre verificato sui prezzi del registro (ADR-024).

Ordine dei candidati: lista Nasdaq Nordic (attivi) -> yf.Search(ISIN) -> ricerca per nome.
Un candidato è accettato solo se i prezzi degli acquisti/vendite on-venue in SEK del registro
cadono nel [Low, High] raw di Yahoo (±tolleranza) per almeno l'80% di almeno 3 righe.
Con meno di 3 righe il ticker `.ST` resta `verified=None` (usabile, segnalato).
Quotazioni solo estere: rifiutate. Nessun ticker viene indovinato.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

import pandas as pd

from . import yf_cache
from .prices import verify_against_register

ON_VENUE_FOR_VERIFY = ("xsto", "fnse", "spotlight", "ngm", "mtf_si")
NAME_SEARCH_MAX_CANDIDATES = 3


@dataclass
class Resolution:
    isin: str
    issuer_key: str
    issuer_name: str
    symbol: str | None
    method: str | None
    verified: bool | None
    n_checked: int
    share_in_range: float | None
    share_in_range_recent: float | None
    median_ratio: float | None
    reason: str
    adjusted_history: bool
    scale_segments: str
    tried: str
    history_start: str | None
    history_end: str | None


def verification_trades(df: pd.DataFrame) -> pd.DataFrame:
    m = (
        df["txn_kind"].isin(["acq_purchase", "disp_sale"])
        & df["venue_class"].isin(ON_VENUE_FOR_VERIFY)
        & df["currency"].eq("SEK")
        & df["volume_unit"].eq("antal")
        & (df["price"].fillna(0) > 0)
        & df["chain_status"].eq("current")
    )
    return df.loc[m, ["isin", "trade_date", "price"]]


def share_isin_universe(df: pd.DataFrame) -> pd.DataFrame:
    shares = df[df["instrument_type"].eq("share") & df["isin_valid"]]
    agg = shares.groupby("isin").agg(
        issuer_key=("issuer_key", lambda s: s.mode().iat[0]),
        issuer_name=("issuer_name_raw", lambda s: s.mode().iat[0]),
        n_rows=("record_id", "size"),
        last_pub=("published_at", "max"),
        first_pub=("published_at", "min"),
    )
    return agg.reset_index()


_NAME_NOISE = re.compile(r"\(publ\)|\bpubl\b|\baktiebolag(et)?\b|\bab\b|\bser\.?\s*[a-d]\b|[,.]", re.IGNORECASE)


def clean_name(name: str) -> str:
    return re.sub(r"\s+", " ", _NAME_NOISE.sub(" ", name or "")).strip()


def resolve_isin(isin: str, issuer_key: str, issuer_name: str, trades: pd.DataFrame, nasdaq_map: dict[str, str], rc: dict) -> Resolution:
    tried: list[str] = []
    best_none: tuple[str, str, object, pd.DataFrame] | None = None

    def attempt(symbol: str, method: str):
        nonlocal best_none
        if symbol in {t.split(":")[0] for t in tried}:
            return None
        if not symbol.endswith(".ST"):
            tried.append(f"{symbol}:FOREIGN_ONLY")
            return None
        hist = yf_cache.history(symbol)
        ver = verify_against_register(hist, trades, rc["price_tolerance"], rc["min_rows_verify"], rc["min_share_verified"])
        tried.append(f"{symbol}:{ver.reason}")
        if ver.verified is True:
            return symbol, method, ver, hist
        if ver.verified is None and hist is not None and best_none is None:
            best_none = (symbol, method, ver, hist)
        return None

    def done(found) -> Resolution:
        symbol, method, ver, hist = found
        segs = ";".join(f"{sg.start.date()}..{sg.end.date()}:{sg.factor:.4f}:{sg.n}" for sg in ver.segments)
        return Resolution(isin, issuer_key, issuer_name, symbol, method, ver.verified, ver.n_checked, ver.share_in_range,
                          ver.share_in_range_recent, ver.median_ratio, ver.reason, ver.adjusted_history, segs, ";".join(tried),
                          str(hist.index.min().date()), str(hist.index.max().date()))

    if isin in nasdaq_map:
        found = attempt(nasdaq_map[isin], "nasdaq_list")
        if found:
            return done(found)
    for q in yf_cache.search_isin(isin):
        sym = q.get("symbol")
        if isinstance(sym, str):
            found = attempt(sym, "search_isin")
            if found:
                return done(found)
    if best_none is None:
        st_symbols = [q.get("symbol") for q in yf_cache.search_text(clean_name(issuer_name))]
        st_symbols = [s for s in st_symbols if isinstance(s, str) and s.endswith(".ST")][:NAME_SEARCH_MAX_CANDIDATES]
        for sym in st_symbols:
            found = attempt(sym, "search_name")
            if found:
                return done(found)
    if best_none is not None:
        return done(best_none)
    reason = "NO_CANDIDATE" if not tried else "NOT_VERIFIED"
    return Resolution(isin, issuer_key, issuer_name, None, None, False, 0, None, None, None, reason, False, "", ";".join(tried), None, None)


def resolve_all(
    df: pd.DataFrame,
    nasdaq: pd.DataFrame,
    rc: dict,
    done: pd.DataFrame | None = None,
    progress=None,
    shard: int | None = None,
    nshards: int = 1,
) -> pd.DataFrame:
    universe = share_isin_universe(df)
    trades = verification_trades(df)
    by_isin = {k: g for k, g in trades.groupby("isin")}
    nasdaq_map = dict(zip(nasdaq["isin"], nasdaq["yahoo"])) if not nasdaq.empty else {}
    already = set(done["isin"]) if done is not None and not done.empty else set()
    out = [] if done is None else done.drop_duplicates("isin").to_dict("records")
    empty = trades.iloc[:0]
    for i, row in enumerate(universe.itertuples(index=False)):
        if row.isin in already or (shard is not None and i % nshards != shard):
            continue
        res = resolve_isin(row.isin, row.issuer_key, row.issuer_name, by_isin.get(row.isin, empty), nasdaq_map, rc)
        out.append(asdict(res))
        if progress:
            progress(i + 1, len(universe), res)
    res_df = pd.DataFrame(out)
    return universe.merge(res_df.drop(columns=["issuer_key", "issuer_name"]), on="isin", how="left")
