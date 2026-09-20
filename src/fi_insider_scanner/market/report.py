"""Checkpoint 4 report: coverage of the ISIN -> ticker resolution."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from ..mdtable import md_table


def _status(v) -> str:
    if v is True:
        return "verificato"
    if v is False:
        return "non risolto"
    return "risolto non verificabile (<3 righe)"


def _segment(df: pd.DataFrame) -> pd.Series:
    on = df[df["venue_class"].isin(["xsto", "fnse", "spotlight", "ngm"])]
    return on.groupby("isin")["venue_class"].agg(lambda s: s.mode().iat[0])


def build_report(res: pd.DataFrame, canonical: pd.DataFrame, a: pd.DataFrame | None, b: pd.DataFrame | None) -> str:
    res = res.copy()
    res["stato"] = res["verified"].map(lambda v: _status(True if v is True or v == 1 else False if v is False or v == 0 else None))
    res["anno ultima attività"] = pd.to_datetime(res["last_pub"]).dt.year.astype(str)
    res["segmento"] = res["isin"].map(_segment(canonical)).fillna("solo fuori mercato/estero")
    out: list[str] = []
    w = out.append
    w("# 03 — Risoluzione ISIN → ticker Yahoo\n")
    w(
        f"Generato {datetime.now(UTC).isoformat(timespec='seconds')}. Universo: ISIN con righe azionarie valide nel registro. "
        "Un ticker è `verificato` se i prezzi on-venue in SEK del registro cadono nel range giornaliero Yahoo (±2%) per ≥ 80% di ≥ 3 righe.\n"
    )
    w("## Esito per ISIN\n")
    w(md_table(res["stato"].value_counts().rename_axis("stato").reset_index(name="ISIN")))
    w("\n## Metodo del ticker accettato\n")
    w(md_table(res["method"].fillna("(nessuno)").value_counts().rename_axis("metodo").reset_index(name="ISIN")))
    w("\n## Motivo dell'esito\n")
    w(md_table(res["reason"].fillna("(n/d)").value_counts().rename_axis("motivo").reset_index(name="ISIN")))
    w("\n## Copertura per anno dell'ultima attività nel registro\n")
    w("Qui si vede la survivorship: gli emittenti spariti presto non hanno serie Yahoo.\n")
    t = pd.crosstab(res["anno ultima attività"], res["stato"])
    t["% verificato"] = (t.get("verificato", 0) / t.sum(axis=1) * 100).round(1)
    w(md_table(t, index=True, digits=1))
    w("\n## Copertura per segmento\n")
    t = pd.crosstab(res["segmento"], res["stato"])
    t["% verificato"] = (t.get("verificato", 0) / t.sum(axis=1) * 100).round(1)
    w(md_table(t, index=True, digits=1))
    for name, ev in (("A (eventi dry-run)", a), ("B (trigger dry-run)", b)):
        if ev is None or ev.empty:
            continue
        m = ev.merge(res[["isin", "stato"]], on="isin", how="left")
        m["stato"] = m["stato"].fillna("ISIN mancante/non azionario")
        w(f"\n## Copertura degli eventi {name} per anno\n")
        t = pd.crosstab(m["event_day"].dt.year.astype(str), m["stato"])
        t["% verificato"] = (t.get("verificato", 0) / t.sum(axis=1) * 100).round(1)
        w(md_table(t, index=True, digits=1))
    ok = res[res["stato"] == "verificato"]
    if not ok.empty:
        w("\n## 30 risoluzioni verificate estratte a caso (audit manuale)\n")
        s = ok.sample(min(30, len(ok)), random_state=11)
        w(md_table(s[["isin", "issuer_name", "symbol", "method", "n_checked", "share_in_range", "median_ratio"]], digits=3))
    bad = res[res["stato"] == "non risolto"].sort_values("n_rows", ascending=False)
    if not bad.empty:
        w("\n## ISIN non risolti con più righe nel registro (primi 40)\n")
        b2 = bad.head(40).copy()
        b2["tried"] = b2["tried"].fillna("").str.slice(0, 90)
        w(md_table(b2[["isin", "issuer_name", "n_rows", "anno ultima attività", "reason", "tried"]]))
    return "\n".join(out) + "\n"
