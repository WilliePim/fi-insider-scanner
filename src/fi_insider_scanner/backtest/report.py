"""Rendering markdown dei checkpoint 5-10. Linguaggio descrittivo; il verdetto vive solo in 20_verdict.md."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..mdtable import md_table
from .stats import Summary, t_iid

FORMULAS = """### Formule usate

- Rendimento evento: r = Close(uscita) / Close(ingresso) − 1 (Close split-adjusted, senza dividendi).
- Eccesso: e = r − r_OMXSPI sulle stesse date di ingresso e uscita. Eccesso contro il peer: e_C = r_evento − r_peer.
- t iid = media / (sd / √n), sd con n − 1.
- t CR1 per cluster g: V = G/(G−1) · Σ_g (Σ_{i∈g} (x_i − media))² / n², t = media / √V; non calcolato con meno di 10 cluster.
- t two-way (emittente, mese di evento): V = V_emittente + V_mese − V_intersezione.
- Calendar-time: per ogni mese di calendario, media equal-weight degli eccessi mensili degli eventi in portafoglio; t iid sulla serie mensile.
- CI 95%: bootstrap percentile sugli eventi, 1.000 estrazioni, seed 12345.
- MDE (α 5% bilaterale, potenza 80%) = (1,96 + 0,84) · sd / √n.
- Costo API di modelli linguistici: 0 token, 0 USD (nessuna chiamata in nessun passo).
"""


def _nan(x) -> bool:
    return x is None or (isinstance(x, float) and np.isnan(x))


def pct(x, sign: bool = True) -> str:
    return "—" if _nan(x) else (f"{x:+.2%}" if sign else f"{x:.2%}")


def num(x, digits: int = 2) -> str:
    return "—" if _nan(x) else f"{x:.{digits}f}"


def flags(s: Summary) -> str:
    out = []
    if s.n < 30:
        out.append("n < 30")
    t = s.t_cr1_issuer if s.t_cr1_issuer is not None else s.t_iid
    if t is None or abs(t) < 2:
        out.append("t < 2")
    if s.mde is not None and s.mean is not None and abs(s.mean) < s.mde:
        out.append("sotto MDE")
    return ", ".join(out)


def summary_table(rows: list[tuple[str, Summary]]) -> str:
    data = [
        (
            label, s.n, pct(s.mean), pct(s.median), num(s.t_iid), num(s.t_cr1_issuer), num(s.t_cr1_month), num(s.t_two_way),
            "—" if s.ci_low is None else f"[{s.ci_low:+.2%}, {s.ci_high:+.2%}]", pct(s.mde, sign=False), s.n_issuers, flags(s),
        )
        for label, s in rows
    ]
    cols = ["cella", "n", "media", "mediana", "t iid", "t CR1 emittente", "t CR1 mese", "t two-way", "CI 95%", "MDE", "emittenti", "note"]
    return md_table(pd.DataFrame(data, columns=cols))


def per_year_table(events: pd.DataFrame, value_col: str, status_col: str) -> str:
    ok = events[events[status_col].eq("OK") & events[value_col].notna()]
    rows = []
    for year, vals in ok.groupby(ok["event_day"].dt.year)[value_col]:
        v = vals.astype(float).to_numpy()
        rows.append((str(year), len(v), pct(float(v.mean())), pct(float(np.median(v))), num(t_iid(v)), "n < 30" if len(v) < 30 else ""))
    return md_table(pd.DataFrame(rows, columns=["anno", "n", "media", "mediana", "t iid", "note"]))


def counts_table(series: pd.Series, name: str) -> str:
    return md_table(series.fillna("(null)").astype(str).value_counts().rename_axis(name).reset_index(name="n"))


def funnel_table(steps: list[tuple[str, int]]) -> str:
    return md_table(pd.DataFrame([(k, int(v)) for k, v in steps], columns=["passo", "eventi"]))


def by_year_crosstab(events: pd.DataFrame, col: str) -> str:
    t = pd.crosstab(events["event_day"].dt.year.astype(str), events[col].fillna("(null)").astype(str))
    t.loc["totale"] = t.sum()
    return md_table(t, index=True, digits=0)


def band_edges_sek(usdsek: pd.Series, low: float, high: float, years) -> str:
    rows = []
    for y in years:
        s = usdsek[usdsek.index.year == int(y)]
        if s.empty:
            continue
        m = float(s.mean())
        rows.append((str(y), num(m, 3), f"{low * m / 1e6:,.0f}", f"{high * m / 1e6:,.0f}"))
    return md_table(pd.DataFrame(rows, columns=["anno", "USDSEK medio", "bordo basso (M SEK)", "bordo alto (M SEK)"]))
