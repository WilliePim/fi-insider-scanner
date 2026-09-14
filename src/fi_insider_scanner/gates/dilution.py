"""Dilution veto svedese (ADR-019), solo informazione visibile a `as_of`.

BLOCKED se:
- partecipazione: Teckning / strumenti di emissione con data in [ultimo acquisto - 5 gg, ultimo acquisto]
- trappola: idem con data in (ultimo acquisto, +75 gg], purché già visibile
- crescita azioni >= 25% su ~1 anno
CAUTION se crescita >= 10%. UNKNOWN se nessun dato azioni e nessun blocco. Altrimenti CLEAR.

Crescita: ultima osservazione `shares_full` disponibile (data + lag <= as_of) contro la
baseline più vicina a un anno prima con distanza 180-700 giorni, normalizzata per gli split.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .structural import issue_rows


@dataclass(frozen=True)
class DilutionVerdict:
    verdict: str  # BLOCKED / CAUTION / CLEAR / UNKNOWN
    participation: bool
    trap: bool
    growth: float | None


def share_growth(shares: pd.Series | None, splits: pd.Series | None, as_of: pd.Timestamp, dc: dict) -> float | None:
    """`shares`: indice data osservazione, valori azioni as-reported. `splits`: indice data, rapporto."""
    if shares is None or shares.empty:
        return None
    available = shares[shares.index <= as_of.normalize() - pd.Timedelta(days=dc["shares_lag_days"])]
    if available.empty:
        return None
    d1, s1 = available.index[-1], float(available.iloc[-1])
    target = d1 - pd.Timedelta(days=365)
    gaps = (d1 - available.index).days
    ok = available[(gaps >= dc["baseline_gap_min_days"]) & (gaps <= dc["baseline_gap_max_days"])]
    if ok.empty or s1 <= 0:
        return None
    pos = int(abs((ok.index - target).days).argmin())
    d0, s0 = ok.index[pos], float(ok.iloc[pos])
    if s0 <= 0:
        return None
    factor = 1.0
    if splits is not None and not splits.empty:
        between = splits[(splits.index > d0) & (splits.index <= d1)]
        for ratio in between:
            factor *= float(ratio)
    return s1 / (s0 * factor) - 1.0


def dilution_verdict(
    v: pd.DataFrame,
    last_buy: pd.Timestamp,
    as_of: pd.Timestamp,
    dc: dict,
    shares: pd.Series | None = None,
    splits: pd.Series | None = None,
) -> DilutionVerdict:
    issues = issue_rows(v)
    lb = last_buy.normalize()
    participation = bool(((issues["trade_date"] >= lb - pd.Timedelta(days=dc["participation_days"])) & (issues["trade_date"] <= lb)).any())
    trap = bool(((issues["trade_date"] > lb) & (issues["trade_date"] <= lb + pd.Timedelta(days=dc["trap_days"]))).any())
    growth = share_growth(shares, splits, as_of, dc)
    if participation or trap or (growth is not None and growth >= dc["growth_blocked"]):
        verdict = "BLOCKED"
    elif growth is not None and growth >= dc["growth_caution"]:
        verdict = "CAUTION"
    elif growth is None:
        verdict = "UNKNOWN"
    else:
        verdict = "CLEAR"
    return DilutionVerdict(verdict, participation, trap, growth)
