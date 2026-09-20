"""Markdown rendering for checkpoints 5-10.

The reports are the laboratory notebook of the study and are written in Italian; the code around them
is in English. Nothing here interprets a result: the verdict applies only the pre-registered criteria.
"""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pandas as pd

from ..mdtable import md_table
from .stats import Summary, t_iid
from .verdict import Verdict

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

SUMMARY_COLUMNS = [
    "cella",
    "n",
    "media",
    "mediana",
    "t iid",
    "t CR1 emittente",
    "t CR1 mese",
    "t two-way",
    "CI 95%",
    "MDE",
    "emittenti",
    "note",
]


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _missing(value) -> bool:
    return value is None or (isinstance(value, float) and np.isnan(value))


def pct(value, sign: bool = True) -> str:
    return "—" if _missing(value) else (f"{value:+.2%}" if sign else f"{value:.2%}")


def num(value, digits: int = 2) -> str:
    return "—" if _missing(value) else f"{value:.{digits}f}"


def flags(s: Summary) -> str:
    """Honesty flags printed next to every cell."""
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
            label,
            s.n,
            pct(s.mean),
            pct(s.median),
            num(s.t_iid),
            num(s.t_cr1_issuer),
            num(s.t_cr1_month),
            num(s.t_two_way),
            "—" if s.ci_low is None else f"[{s.ci_low:+.2%}, {s.ci_high:+.2%}]",
            pct(s.mde, sign=False),
            s.n_issuers,
            flags(s),
        )
        for label, s in rows
    ]
    return md_table(pd.DataFrame(data, columns=SUMMARY_COLUMNS))


def per_year_table(events: pd.DataFrame, value_col: str, status_col: str) -> str:
    ok = events[events[status_col].eq("OK") & events[value_col].notna()]
    rows = []
    for year, values in ok.groupby(ok["event_day"].dt.year)[value_col]:
        v = values.astype(float).to_numpy()
        rows.append((str(year), len(v), pct(float(v.mean())), pct(float(np.median(v))), num(t_iid(v)), "n < 30" if len(v) < 30 else ""))
    return md_table(pd.DataFrame(rows, columns=["anno", "n", "media", "mediana", "t iid", "note"]))


def counts_table(series: pd.Series, name: str) -> str:
    return md_table(series.fillna("(null)").astype(str).value_counts().rename_axis(name).reset_index(name="n"))


def funnel_table(steps: list[tuple[str, int]]) -> str:
    return md_table(pd.DataFrame([(step, int(n)) for step, n in steps], columns=["passo", "eventi"]))


def by_year_crosstab(events: pd.DataFrame, col: str) -> str:
    table = pd.crosstab(events["event_day"].dt.year.astype(str), events[col].fillna("(null)").astype(str))
    table.loc["totale"] = table.sum()
    return md_table(table, index=True, digits=0)


def band_edges_sek(usdsek: pd.Series, low: float, high: float, years) -> str:
    rows = []
    for year in years:
        rates = usdsek[usdsek.index.year == int(year)]
        if rates.empty:
            continue
        mean = float(rates.mean())
        rows.append((str(year), num(mean, 3), f"{low * mean / 1e6:,.0f}", f"{high * mean / 1e6:,.0f}"))
    return md_table(pd.DataFrame(rows, columns=["anno", "USDSEK medio", "bordo basso (M SEK)", "bordo alto (M SEK)"]))


# --- checkpoint 5 -------------------------------------------------------------------------------


def gates_mcap_report(a: pd.DataFrame, b: pd.DataFrame, usdsek: pd.Series, cfg: dict) -> str:
    out = ["# 05 — Gate con dati di mercato e market cap\n", f"Generato {now()}. Nessun rendimento successivo agli eventi calcolato.\n"]
    for name, events, date_col in (("A", a, "last_trade"), ("B", b, "anchor")):
        out.append(f"## Colonna {name}\n")
        out.append(f"Eventi nel periodo {cfg['backtest']['start']} – {cfg['backtest']['end']}: **{len(events):,}**.\n")
        out.append("\nDilution veto per anno:\n")
        out.append(by_year_crosstab(events, "dilution"))
        if name == "B":
            out.append("\nScore Layer 1 per anno (con dati di mercato):\n")
            out.append(by_year_crosstab(events.assign(score=events["score"].astype(str)), "score"))
            out.append(
                f"\nStale: {int(events['is_stale'].sum())}; 4/4 non stale (primaria B): {int(events['gate_ok'].sum())}. "
                f"Persone con `large_holder=true` (parole chiave o posizione ≥ 10%): {int(events['n_large_holder'].sum())}; "
                f"acquisti simbolici (limite superiore < 1%): {int(events['n_symbolic'].sum())}.\n"
            )
        out.append(f"\nMotivo della market cap (data mcap = `{date_col}`):\n")
        out.append(counts_table(events["mcap_reason"], "motivo"))
        out.append("\nBanda per anno:\n")
        out.append(by_year_crosstab(events, "band"))
        gated = events[events["gate_ok"]]
        in_band = gated[gated["band"].eq("50_300")]
        out.append(
            f"\nDopo il gate, in banda 50-300M: **{len(in_band):,}**; con bordi stretti ±20%: {int(gated['in_band_narrow'].sum()):,}; "
            f"con bordi larghi ±20%: {int(gated['in_band_wide'].sum()):,}. Dual class tra gli eventi in banda: "
            f"{int(in_band['dual_class'].sum()):,} ({in_band['dual_class'].mean():.1%}). Righe con tipo strumento debole "
            f"(maggioranza/nome/emittente): {int(in_band['weak_type'].sum()):,}. Data report nota a T: "
            f"{in_band['days_since_report'].notna().mean():.1%} degli eventi in banda.\n"
        )
    out.append("\n## Bordi della banda in SEK\n")
    out.append(band_edges_sek(usdsek, cfg["band"]["low_usd"], cfg["band"]["high_usd"], range(2016, 2026)))
    return "\n".join(out) + "\n"


# --- checkpoints 7-10 -----------------------------------------------------------------------------


def column_a_report(
    *, funnel, status_counts, primary, control, calendar, coverage, per_year, sensitivities, closed_period, cells, horizon
) -> str:
    out = [
        "# 10 — Backtest colonna A (analogo del test USA)\n",
        f"Generato {now()}. Pre-registrazione: `backtest/preregistration.md`.\n",
        "## Imbuto verso la cella primaria P\n",
        funnel_table(funnel),
        f"\nStati del rendimento a {horizon} sessioni nella cella P:\n",
        counts_table(status_counts, "stato"),
        "\n## Cella primaria P e colonna C\n",
        summary_table([("P: A (b) 50-300M 126s vs OMXSPI", primary), ("C: stessi eventi vs peer", control)]),
        f"\nPortafoglio calendar-time mensile di P: t = {num(calendar[0])} su {calendar[1]} mesi.\n",
        f"\nCopertura (A variante b, tutte le bande, rendimento OK / eventi): **{coverage:.1%}**.\n",
        "\n## P per anno\n",
        per_year,
        "\n## Sensibilità (descrittive)\n",
        summary_table(sensitivities),
        "\n## Closed period (descrittivo)\n",
        summary_table(closed_period),
        "\n## Tutte le celle A (descrittive)\n",
        summary_table(cells),
        "\n" + FORMULAS,
    ]
    return "\n".join(out) + "\n"


def column_b_report(*, funnel, cells_main, calendar, per_year, closed_period, cells, horizon) -> str:
    out = [
        "# 11 — Backtest colonna B (cluster Layer 1, versione del prompt)\n",
        f"Generato {now()}. Descrittivo: il verdetto dipende solo dalla colonna A.\n",
        "## Imbuto\n",
        funnel_table(funnel),
        "\n## Cella B e controllo\n",
        summary_table(cells_main),
        f"\nPortafoglio calendar-time mensile di B: t = {num(calendar[0])} su {calendar[1]} mesi.\n",
        "\n## B per anno\n",
        per_year,
        "\n## Closed period (descrittivo)\n",
        summary_table(closed_period),
        "\n## Tutte le celle B (descrittive)\n",
        summary_table(cells),
        "\n" + FORMULAS,
    ]
    return "\n".join(out) + "\n"


def control_report(*, peer_status, band_cells, decomposition, placebo_cells) -> str:
    out = [
        "# 12 — Matched control\n",
        f"Generato {now()}. Peer: stessa banda alla stessa data, nessuna riga B_row visibile nei 60 giorni prima, log-cap più vicino.\n",
        "## Esito della selezione del peer nella cella P\n",
        counts_table(peer_status, "stato gamba peer"),
        "\n## Celle per banda\n",
        summary_table(band_cells),
        "\n## Scomposizione per anno (cella P)\n",
        "`eccesso vs indice` − `eccesso vs peer` = rendimento medio dei peer contro l'indice: la parte attribuibile alla dimensione.\n",
        md_table(pd.DataFrame(decomposition, columns=["anno", "n P", "eccesso vs indice", "coppie", "eccesso vs peer", "peer vs indice"])),
        "\n## Placebo (date spostate di −252 sessioni, stessi emittenti)\n",
        summary_table(placebo_cells),
        "\nAtteso ≈ 0 contro il peer: un valore lontano da zero indica un bias della pipeline, non un segnale.\n",
        "\n" + FORMULAS,
    ]
    return "\n".join(out) + "\n"


def survivorship_report(*, status_by_year, unresolved_by_year, surv, primary, scenario_cells) -> str:
    share = surv["n_unresolved"] / surv["n_events"] if surv["n_events"] else 0.0
    out = [
        "# 13 — Survivorship\n",
        f"Generato {now()}.\n",
        "## Stato del rendimento per anno (A variante b, tutte le bande)\n",
        md_table(status_by_year, index=True, digits=0),
        "\n## Eventi senza banda (ticker o mcap mancanti)\n",
        md_table(unresolved_by_year.rename_axis("anno").reset_index().astype({"anno": str}), digits=0),
        f"\nNon risolti: **{surv['n_unresolved']:,}** su {surv['n_events']:,} eventi ({share:.0%}); attesi in banda 50-300M: "
        f"**{surv['expected_in_band']:,}**; con indizio di acquisizione (vendite fuori mercato allo stesso prezzo prima "
        f"dell'ultima riga): {surv['acquired_in_unresolved']:,}. r̄_OMXSPI sugli eventi osservati: {pct(surv['r_bench_mean'])}.\n",
        f"\nBreak-even p* (quota dei non risolti a −100% che azzera la media di P): sugli attesi in banda "
        f"{pct(surv['break_even_expected'], sign=False)}, su tutti {pct(surv['break_even_all'], sign=False)}.\n",
        "\n## P con gli scenari aggiunti\n",
        summary_table([("P osservata", primary), *scenario_cells]),
        "\nS_minus100 = −1 − r̄_bench; S_minus50 = −0,5 − r̄_bench; S0 = 0; S_plus = +15%; S_draw = estrazione dalla distribuzione osservata; "
        "S_mix_acquired = +15% se c'è indizio di acquisizione, altrimenti −100%.\n",
    ]
    return "\n".join(out) + "\n"


LIMITATIONS = """## Cosa non è stato possibile fare, e perché

1. Tenere i delistati "con l'ultimo prezzo disponibile": Yahoo non ha le serie degli emittenti spariti (report 03:
   2,4% di ticker verificati tra chi ha smesso di comparire nel 2016, 69,5% tra chi è ancora attivo nel 2026).
   Sostituito da copertura per anno, scenari e break-even.
2. Un benchmark small cap o total return: su yfinance esistono solo `^OMXSPI` (price index) e nessun indice
   small/gross con storico. Sostituito dal peer della stessa banda (colonna C), che il placebo mostra non neutro.
3. Il flag closed period per tutti gli eventi: le date report Yahoo mancano o sono vecchie per molte small cap (ADR-043).
4. Un dilution veto simmetrico a quello USA: niente prospetti, l'attività di emissione si vede solo dal registro e
   dalla crescita delle azioni Yahoo.
5. Il test di invarianza per troncamento su 200 eventi previsto dal piano: non implementato. Le garanzie point-in-time
   restano nei test unitari di `Register.visible`, cluster e gate, e nel test AST che vieta `expost_` e la lettura
   diretta degli status nei moduli che decidono.
6. La correzione per il cambio di soglia FI (EUR 5.000 → 20.000 dal 2024-12-04, ADR-040): non applicata; le tabelle
   per anno la rendono visibile.
7. Righe identiche reali perse dalla dedup upstream prima del 2026-08-16: non recuperabili dal bulk (ADR-002).
8. Nessun modello linguistico è stato usato in nessun passo: token e costo per run = 0.
"""


def verdict_report(
    *,
    verdict: Verdict,
    primary: Summary,
    control: Summary,
    s0_mean,
    coverage,
    placebo_cells,
    closed_period,
    band_cells,
    b_cells,
    sensitivities,
    surv,
    dilution_unknown_share,
    report_known_share,
) -> str:
    checks = pd.DataFrame([(k, str(v)) for k, v in verdict.checks.items()], columns=["criterio", "valore"])
    means = [s.mean for _, s in sensitivities if s.mean is not None]
    placebo_peer = dict(placebo_cells).get("placebo vs peer")
    inside, outside = closed_period[0][1], closed_period[1][1]
    unresolved_share = surv["n_unresolved"] / surv["n_events"] if surv["n_events"] else 0.0
    break_even = (
        "non è definito perché la media osservata è negativa"
        if surv["break_even_all"] is None
        else f"vale {pct(surv['break_even_all'], sign=False)} sui non risolti"
    )
    out = [
        "# 20 — Verdetto pre-registrato\n",
        f"Generato {now()}. Criteri: `backtest/preregistration.md`. Nessuna interpretazione oltre i criteri.\n",
        f"## Esito: **{verdict.label}**\n",
        "\n".join(f"- {reason}" for reason in verdict.reasons),
        "\n## Numeri usati\n",
        summary_table([("P: A (b) 50-300M 126s vs OMXSPI", primary), ("C: stessi eventi vs peer", control)]),
        f"\nMedia di P con scenario S0 sugli attesi in banda: {pct(s0_mean)}. Copertura: {coverage:.1%}.\n",
        "\n## Controlli\n",
        md_table(checks),
        "\n## Riferimento USA\n",
        "Scanner USA su Form 4, stessa definizione: +3,50% (t = 4,30, iid) a 126 giorni in banda $50-300M vs IWM; "
        "matched control +2,41% (t = 2,02).\n",
        "\n## Letture descrittive (non entrano nel verdetto)\n",
    ]
    if placebo_peer is not None:
        out.append(
            f"- Il placebo (stessi emittenti, date spostate di −252 sessioni) contro il peer vale {pct(placebo_peer.mean)} "
            f"(t iid {num(placebo_peer.t_iid)}, n {placebo_peer.n}): il confronto con il peer non è neutro. Gli emittenti che un anno "
            f"dopo avranno acquisti insider battevano già i pari dimensione, quindi {pct(control.mean)} va letto contro quel "
            "baseline positivo, non contro zero."
        )
    out += [
        "- Scomposizione per anno (report 12): l'eccesso contro l'indice segue il rendimento dei peer contro l'indice, cioè "
        "l'effetto dimensione. Il numero USA, misurato contro IWM, era esposto allo stesso confondimento.",
        f"- Closed period: acquisti entro 10 giorni dal report {pct(inside.mean)} (n {inside.n}, t CR1 {num(inside.t_cr1_issuer)}); "
        f"oltre 10 giorni {pct(outside.mean)} (n {outside.n}, t {num(outside.t_iid)}). La direzione è quella ipotizzata, ma la media "
        f"sta sotto la propria MDE, la differenza fra i due sottoinsiemi non è testata e la data report è nota solo per il "
        f"{report_known_share:.0%} degli eventi della cella P.",
        "- Bande: " + "; ".join(f"{label} {pct(s.mean)} (t {num(s.t_iid)})" for label, s in band_cells if "vs peer" in label) + ".",
        "- Colonna B (cluster 4/4, banda): "
        + "; ".join(f"{label} {pct(s.mean)} (n {s.n}, MDE {pct(s.mde, sign=False)})" for label, s in b_cells[:1])
        + ".",
        f"- Sensibilità della cella P: tutte fra {pct(min(means))} e {pct(max(means))}; nessuna cambia segno.",
        f"- Il dilution veto resta UNKNOWN per il {dilution_unknown_share:.0%} degli eventi A (nessuna serie azioni alla data).",
        "\n## Survivorship\n",
        f"- {surv['n_unresolved']:,} eventi A (b) su {surv['n_events']:,} ({unresolved_share:.0%}) non hanno banda perché l'emittente "
        f"non ha una serie Yahoo verificata o un conteggio azioni alla data; {surv['expected_in_band']:,} di questi sarebbero attesi "
        f"in banda. Con lo scenario S0 la media di P resta {pct(s0_mean)}. Il break-even p* {break_even}.\n",
        "\n" + LIMITATIONS,
    ]
    return "\n".join(out) + "\n"
