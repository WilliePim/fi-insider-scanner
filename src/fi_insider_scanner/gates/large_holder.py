"""Grande azionista e acquisto simbolico (ADR-012, ADR-020).

MAR art. 19 non copre i detentori >10%, quindi il registro non può dire "non è grande
azionista". Il flag vale "true" (parola chiave nel ruolo, oppure posizione minima visibile
>= 10% delle azioni) oppure "unknown": mai "false".

`position_lb` = somma netta dei volumi azionari visibili della persona (veicoli inclusi)
dal 2016-07: è un limite inferiore della posizione vera, perché gli acquisti precedenti al
registro non si vedono.
"""

from __future__ import annotations

import pandas as pd


def position_lb(v: pd.DataFrame, person_key: str, isin: str | None = None) -> float:
    own = v[v["person_key"].eq(person_key) & v["instrument_type"].eq("share") & v["volume_unit"].eq("antal")]
    if isin is not None:
        own = own[own["isin"].eq(isin)]
    net = float((own["direction"] * own["volume"].fillna(0)).sum())
    return max(net, 0.0)


def large_holder(v: pd.DataFrame, person_key: str, shares_outstanding: float | None, threshold: float) -> str:
    own = v[v["person_key"].eq(person_key)]
    if any("owner_keyword" in r for r in own["roles"]):
        return "true"
    if shares_outstanding and shares_outstanding > 0 and position_lb(v, person_key) >= threshold * shares_outstanding:
        return "true"
    return "unknown"


def symbolic_purchase(v_before: pd.DataFrame, person_key: str, volume: float, max_change: float) -> str:
    """True se il limite superiore della variazione % (volume / posizione minima) è sotto la soglia."""
    lb = position_lb(v_before, person_key)
    if lb <= 0:
        return "unknown"
    return "true" if volume / lb < max_change else "unknown"
