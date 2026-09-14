"""Predicati di riga per il segnale (ADR-016) e motivi di esclusione.

- base: Förvärv + azione (dichiarata o inferita) + non programma + prezzo > 0 + volume in Antal
- A_exact:   base + valore >= soglia USD (parità col codice P USA, qualunque venue)
- A_onvenue: A_exact + venue di negoziazione
- B_row:     base + venue di negoziazione (nessuna soglia)
Le funzioni lavorano su righe già filtrate da `Register.visible()`.
"""

from __future__ import annotations

import pandas as pd

from ..canon.taxonomy import EXCLUSION_BY_KIND, TxnKind, VenueClass

OFF_VENUE_CLASSES = (str(VenueClass.OFF_VENUE), str(VenueClass.UNKNOWN))
PURCHASE = str(TxnKind.ACQ_PURCHASE)


def base_purchase(v: pd.DataFrame) -> pd.Series:
    return (
        v["txn_kind"].eq(PURCHASE)
        & v["instrument_type"].eq("share")
        & ~v["is_share_program"].eq(True)
        & (v["price"].fillna(0) > 0)
        & (v["volume"].fillna(0) > 0)
        & v["volume_unit"].eq("antal")
    )


def on_venue(v: pd.DataFrame) -> pd.Series:
    return ~v["venue_class"].isin(OFF_VENUE_CLASSES)


def a_exact(v: pd.DataFrame, min_usd: float) -> pd.Series:
    return base_purchase(v) & v["value_usd"].ge(min_usd).fillna(False).astype(bool)


def a_onvenue(v: pd.DataFrame, min_usd: float) -> pd.Series:
    return a_exact(v, min_usd) & on_venue(v)


def b_row(v: pd.DataFrame) -> pd.Series:
    return base_purchase(v) & on_venue(v)


def exclusion_reason(v: pd.DataFrame) -> pd.Series:
    """Perché una riga non è un acquisto base. Vuoto = acquisto base."""
    kinds = {str(k): r for k, r in EXCLUSION_BY_KIND.items()}
    reason = v["txn_kind"].map(kinds).fillna("").astype("object")
    purchase = v["txn_kind"].eq(PURCHASE)

    def assign(mask: pd.Series, label: str) -> None:
        sel = purchase & reason.eq("") & mask
        reason[sel] = label

    assign(v["is_share_program"].eq(True), "share_program")
    assign(v["instrument_type"].isna(), "instrument_type_unknown")
    assign(~v["instrument_type"].eq("share") & v["instrument_type"].notna(), "non_share")
    assign(v["volume_unit"].eq("belopp"), "amount_unit")
    assign(~(v["price"].fillna(0) > 0), "zero_or_missing_price")
    assign(~(v["volume"].fillna(0) > 0), "zero_or_missing_volume")
    return reason


def sell_to_cover_candidates(v: pd.DataFrame, window_days: int) -> pd.Series:
    """Avyttring entro `window_days` da un Tilldelning / Lösen ökning / riga di programma della stessa persona."""
    sales = v[v["txn_kind"].eq(str(TxnKind.DISP_SALE))]
    triggers = v[v["txn_kind"].isin([str(TxnKind.GRANT), str(TxnKind.EXERCISE_IN)]) | v["is_share_program"].eq(True)]
    out = pd.Series(False, index=v.index)
    if sales.empty or triggers.empty:
        return out
    trig = triggers.groupby(["issuer_key", "name_key"])["trade_date"].apply(lambda s: s.sort_values().to_numpy())
    window = pd.Timedelta(days=window_days)
    for idx, issuer, person, day in zip(sales.index, sales["issuer_key"], sales["name_key"], sales["trade_date"]):
        arr = trig.get((issuer, person))
        if arr is None or pd.isna(day):
            continue
        pos = int(arr.searchsorted(day.to_datetime64(), side="right"))
        if pos > 0 and (day - pd.Timestamp(arr[pos - 1])) <= window:
            out.at[idx] = True
    return out
