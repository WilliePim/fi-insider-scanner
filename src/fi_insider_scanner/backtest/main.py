"""Orchestrazione dei checkpoint 6 (gate + mcap), 6b (pre-registrazione) e 7-10 (rendimenti, control,
survivorship, placebo, verdetto)."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from .. import config, pipeline, store
from ..market import fx as fxmod
from ..market import yf_cache
from ..market.context import YahooMarket
from . import prereg, run
from . import report as rp
from .control import QuietIndex
from .verdict import decide

DATE_COLS = ("event_day", "as_of", "first_trade", "last_trade", "anchor", "window_end", "shares_date", "entry_date", "exit_date")
BOOL_COLS = (
    "has_onvenue_row", "all_natural", "dil_participation", "dil_trap", "gate_ok", "is_stale", "s3_in_window", "uniform_onvenue",
    "s1_subscription", "s2_issue_instruments", "not_routine", "dilution_ok", "no_large_holder", "in_band_narrow", "in_band_wide",
    "dual_class", "weak_type",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_env(cfg: dict, db_path=None) -> run.Env:
    df = pipeline.canonical_with_values() if db_path is None else pipeline.canonical_from(db_path)
    current = df[df["chain_status"].eq("current")].copy()
    market = YahooMarket(store.load_frame("resolution"))
    bench = yf_cache.history(cfg["backtest"]["benchmark"])["Close"].astype(float)
    return run.Env(cfg, market, bench, fxmod.load_fx()["USD"], current)


def load_events(name: str) -> pd.DataFrame:
    ev = store.load_frame(name)
    for col in DATE_COLS:
        if col in ev:
            ev[col] = pd.to_datetime(ev[col])
    for col in BOOL_COLS:
        if col in ev:
            ev[col] = ev[col].map(lambda v: bool(v) if pd.notna(v) else False)
    if "verified" in ev:
        ev["verified"] = ev["verified"].map(lambda v: None if pd.isna(v) else bool(v))
    if "band" in ev:
        ev["band"] = ev["band"].map(lambda v: None if pd.isna(v) else str(v))
    return ev


# --- checkpoint 6 ---------------------------------------------------------------------------


def gates_mcap(cfg: dict) -> str:
    env = load_env(cfg)
    reg = pipeline.register("snapshot", "pub")
    a = run.column_a(reg, env)
    b = run.column_b(reg, env)
    store.save_frame("events_a", a)
    store.save_frame("events_b", b)
    low, high = cfg["band"]["low_usd"], cfg["band"]["high_usd"]
    out = [f"# 05 — Gate con dati di mercato e market cap\n", f"Generato {_now()}. Nessun rendimento successivo agli eventi calcolato.\n"]
    for name, ev, date_col in (("A", a, "last_trade"), ("B", b, "anchor")):
        out.append(f"## Colonna {name}\n")
        out.append(f"Eventi nel periodo {cfg['backtest']['start']} – {cfg['backtest']['end']}: **{len(ev):,}**.\n")
        out.append("\nDilution veto per anno:\n")
        out.append(rp.by_year_crosstab(ev, "dilution"))
        if name == "B":
            out.append("\nScore Layer 1 per anno (con dati di mercato):\n")
            out.append(rp.by_year_crosstab(ev.assign(score=ev["score"].astype(str)), "score"))
            out.append(f"\nStale: {int(ev['is_stale'].sum())}; 4/4 non stale (primaria B): {int(ev['gate_ok'].sum())}. "
                       f"Persone con `large_holder=true` (parole chiave o posizione ≥ 10%): {int(ev['n_large_holder'].sum())}; "
                       f"acquisti simbolici (limite superiore < 1%): {int(ev['n_symbolic'].sum())}.\n")
        out.append(f"\nMotivo della market cap (data mcap = `{date_col}`):\n")
        out.append(rp.counts_table(ev["mcap_reason"], "motivo"))
        out.append("\nBanda per anno:\n")
        out.append(rp.by_year_crosstab(ev, "band"))
        gated = ev[ev["gate_ok"]]
        inband = gated[gated["band"].eq("50_300")]
        out.append(f"\nDopo il gate, in banda 50-300M: **{len(inband):,}**; con bordi stretti ±20%: {int(gated['in_band_narrow'].sum()):,}; "
                   f"con bordi larghi ±20%: {int(gated['in_band_wide'].sum()):,}. Dual class tra gli eventi in banda: "
                   f"{int(inband['dual_class'].sum()):,} ({inband['dual_class'].mean():.1%}). Righe con tipo strumento debole "
                   f"(maggioranza/nome/emittente): {int(inband['weak_type'].sum()):,}. Data report nota a T: "
                   f"{inband['days_since_report'].notna().mean():.1%} degli eventi in banda.\n")
    out.append("\n## Bordi della banda in SEK\n")
    out.append(rp.band_edges_sek(env.usdsek, low, high, range(2016, 2026)))
    md = "\n".join(out) + "\n"
    (config.BACKTEST_DIR / "05_gates_mcap.md").write_text(md, encoding="utf-8")
    return md


# --- checkpoint 6b --------------------------------------------------------------------------


def freeze(cfg: dict) -> str:
    md = prereg.build(cfg)
    (config.BACKTEST_DIR / "preregistration.md").write_text(md, encoding="utf-8")
    return md


# --- checkpoint 7-10 ------------------------------------------------------------------------


def _last_flat(events: pd.DataFrame, value: str, status: str) -> pd.DataFrame:
    tmp = events[events[status].isin(["OK", "ENDED_IN_WINDOW"])].copy()
    tmp["v_last_flat"] = np.where(tmp[status].eq("OK"), tmp[value], tmp["excess_last_flat"])
    tmp["st_last_flat"] = "OK"
    return tmp


def _cells_by_band(ev: pd.DataFrame, cfg: dict, prefix: str) -> list[tuple[str, object]]:
    rows = []
    for band in run.BANDS + (None,):
        for variant in ("b", "a"):
            sel = run.select(ev, band, cfg, variant)
            for hh in cfg["backtest"]["horizons"]:
                rows.append((f"{prefix} ({variant}) {band or 'tutte'} {hh}s", run.cell(sel, f"excess_{hh}", cfg, f"status_{hh}")))
    return rows


def _closed_period(ev: pd.DataFrame, cfg: dict, label: str, value: str) -> list[tuple[str, object]]:
    from ..gates.closed_period import MAX_REPORT_GAP_DAYS

    rows = []
    # lista report incompleta (ultima data > 200 gg prima di T) -> UNKNOWN (ADR-043)
    d = ev["days_since_report"].where(ev["days_since_report"] <= MAX_REPORT_GAP_DAYS)
    for w in (cfg["closed_period"]["window_days_primary"], cfg["closed_period"]["window_days_descriptive"]):
        rows.append((f"{label}: dentro finestra post-report ≤ {w} gg", run.cell(ev[d.notna() & (d <= w)], value, cfg)))
        rows.append((f"{label}: fuori finestra (> {w} gg)", run.cell(ev[d.notna() & (d > w)], value, cfg)))
    rows.append((f"{label}: data report UNKNOWN", run.cell(ev[d.isna()], value, cfg)))
    return rows


def backtest(cfg: dict) -> dict:
    bt = cfg["backtest"]
    h = bt["primary_horizon"]
    H, S = f"excess_{h}", f"status_{h}"
    env = load_env(cfg)
    reg = pipeline.register("snapshot", "pub")
    a = run.attach_returns(load_events("events_a"), env)
    b = run.attach_returns(load_events("events_b"), env)
    for ev in (a, b):
        ev["excess_net"] = ev[H] - bt["cost_bps"] / 10_000

    gated_a, gated_b = a[a["gate_ok"]], b[b["gate_ok"]]
    quiet = QuietIndex(reg)
    dates = pd.DatetimeIndex(pd.concat([gated_a.loc[gated_a["band"].notna(), "last_trade"], gated_b.loc[gated_b["band"].notna(), "anchor"]]))
    pool = run.Pool(env, dates)
    ca = run.attach_control(gated_a, env, quiet, pool, "last_trade")
    cb = run.attach_control(gated_b, env, quiet, pool, "anchor")
    ca.to_csv(config.BACKTEST_DIR / "10_events_A.csv", index=False)
    cb.to_csv(config.BACKTEST_DIR / "11_events_B.csv", index=False)

    # --- colonna A ---
    P_events = run.select(ca, "50_300", cfg, "b")
    P = run.cell(P_events, H, cfg)
    C = run.cell(P_events, "excess_vs_peer", cfg)
    ct_t, ct_n = run.calendar_time(P_events[P_events[S].eq("OK")], env)
    all_b = run.select(ca, None, cfg, "b")
    coverage = float(all_b[S].eq("OK").mean()) if len(all_b) else 0.0
    surv = run.survivorship_table(all_b, P_events[P_events[S].eq("OK")], env)
    s0 = surv["table"]
    s0_mean = s0[(s0["ambito"] == "attesi_in_banda") & (s0["scenario"] == "S0")]["mean"]
    s0_mean = float(s0_mean.iloc[0]) if len(s0_mean) and pd.notna(s0_mean.iloc[0]) else None
    verdict = decide(P, C, s0_mean, coverage, bt["min_coverage_for_verdict"])

    lf = _last_flat(P_events, H, S)
    sens = [
        ("P primaria", P),
        ("netto 100bp", run.cell(P_events, "excess_net", cfg)),
        ("Adj Close (limite superiore)", run.cell(P_events, "excess_adj", cfg)),
        ("parità di bar (uscita nella serie del titolo)", run.cell(P_events, "excess_own_bars", cfg, "status_own_bars")),
        ("senza expost_rights_issue", run.cell(P_events[~P_events["expost_rights_issue"]], H, cfg)),
        ("senza expost_large_move", run.cell(P_events[~P_events["expost_large_move"]], H, cfg)),
        ("ENDED_IN_WINDOW all'ultimo prezzo", run.cell(lf, "v_last_flat", cfg, "st_last_flat")),
        ("A_onvenue", run.cell(run.select(ca[ca["has_onvenue_row"]], "50_300", cfg, "b"), H, cfg)),
        ("senza dilution gate", run.cell(run.select(a, "50_300", cfg, "b"), H, cfg)),
        ("solo ticker verified=True", run.cell(run.select(ca[ca["verified"].eq(True)], "50_300", cfg, "b"), H, cfg)),
        ("senza emittenti dual class", run.cell(run.select(ca[~ca["dual_class"]], "50_300", cfg, "b"), H, cfg)),
        ("solo tipo strumento dichiarato/unanime", run.cell(run.select(ca[~ca["weak_type"]], "50_300", cfg, "b"), H, cfg)),
        ("banda con bordi stretti ±20%", run.cell(run.select(ca[ca["in_band_narrow"]], None, cfg, "b"), H, cfg)),
        ("banda con bordi larghi ±20%", run.cell(run.select(ca[ca["in_band_wide"]], None, cfg, "b"), H, cfg)),
    ]
    for mode, timing in (("as_seen", "pub"), ("snapshot", "first_pub")):
        alt = run.attach_returns(run.column_a(pipeline.register(mode, timing), env), env)
        sens.append((f"visibilità {mode} + timing {timing}", run.cell(run.select(alt[alt["gate_ok"]], "50_300", cfg, "b"), H, cfg)))
    closed_a = _closed_period(P_events, cfg, "P", H)
    cells_a = _cells_by_band(ca, cfg, "A")

    funnel_a = [
        ("eventi A nel periodo (variante a)", len(a)),
        ("dopo dilution gate", len(gated_a)),
        ("con ticker del proprio ISIN (verified ≠ False)", int(gated_a["symbol"].notna().sum())),
        ("con market cap", int(gated_a["mcap_usd"].notna().sum())),
        ("in banda 50-300M", int(gated_a["band"].eq("50_300").sum())),
        ("variante (b)", len(P_events)),
        (f"rendimento OK a {h} sessioni", int(P_events[S].eq("OK").sum())),
    ]
    txt = [
        "# 10 — Backtest colonna A (analogo del test USA)\n",
        f"Generato {_now()}. Pre-registrazione: `backtest/preregistration.md`.\n",
        "## Imbuto verso la cella primaria P\n", rp.funnel_table(funnel_a),
        f"\nStati del rendimento a {h} sessioni nella cella P:\n", rp.counts_table(P_events[S], "stato"),
        "\n## Cella primaria P e colonna C\n",
        rp.summary_table([("P: A (b) 50-300M 126s vs OMXSPI", P), ("C: stessi eventi vs peer", C)]),
        f"\nPortafoglio calendar-time mensile di P: t = {rp.num(ct_t)} su {ct_n} mesi.\n",
        f"\nCopertura (A variante b, tutte le bande, rendimento OK / eventi): **{coverage:.1%}**.\n",
        "\n## P per anno\n", rp.per_year_table(P_events, H, S),
        "\n## Sensibilità (descrittive)\n", rp.summary_table(sens),
        "\n## Closed period (descrittivo)\n", rp.summary_table(closed_a),
        "\n## Tutte le celle A (descrittive)\n", rp.summary_table(cells_a),
        "\n" + rp.FORMULAS,
    ]
    (config.BACKTEST_DIR / "10_backtest_A.md").write_text("\n".join(txt) + "\n", encoding="utf-8")

    # --- colonna B ---
    B_events = run.select(cb, "50_300", cfg, "b")
    PB = run.cell(B_events, H, cfg)
    CB = run.cell(B_events, "excess_vs_peer", cfg)
    ctb_t, ctb_n = run.calendar_time(B_events[B_events[S].eq("OK")], env)
    nonstale = b[~b["is_stale"]]
    by_score = [(f"score {k} non stale (b) 50-300M", run.cell(run.select(nonstale[nonstale["score"].eq(k)], "50_300", cfg, "b"), H, cfg)) for k in (4, 3, 2, 1, 0)]
    sens_b = [
        ("B primaria: 4/4 non stale (b) 50-300M", PB),
        ("C: stessi eventi vs peer", CB),
        ("senza acquisti simbolici", run.cell(run.select(cb[cb["n_symbolic"].eq(0)], "50_300", cfg, "b"), H, cfg)),
        ("score ≥ 3 non stale", run.cell(run.select(nonstale[nonstale["score"] >= 3], "50_300", cfg, "b"), H, cfg)),
        ("senza expost_rights_issue", run.cell(B_events[~B_events["expost_rights_issue"]], H, cfg)),
        ("Adj Close (limite superiore)", run.cell(B_events, "excess_adj", cfg)),
        ("netto 100bp", run.cell(B_events, "excess_net", cfg)),
    ] + by_score
    txt = [
        "# 11 — Backtest colonna B (cluster Layer 1, versione del prompt)\n",
        f"Generato {_now()}. Descrittivo: il verdetto dipende solo dalla colonna A.\n",
        "## Imbuto\n",
        rp.funnel_table([
            ("trigger B nel periodo", len(b)), ("non stale", len(nonstale)), ("4/4 non stale", len(gated_b)),
            ("con ticker del proprio ISIN", int(gated_b["symbol"].notna().sum())), ("in banda 50-300M", int(gated_b["band"].eq("50_300").sum())),
            ("variante (b)", len(B_events)), (f"rendimento OK a {h} sessioni", int(B_events[S].eq("OK").sum())),
        ]),
        "\n## Cella B e controllo\n", rp.summary_table(sens_b),
        f"\nPortafoglio calendar-time mensile di B: t = {rp.num(ctb_t)} su {ctb_n} mesi.\n",
        "\n## B per anno\n", rp.per_year_table(B_events, H, S),
        "\n## Closed period (descrittivo)\n", rp.summary_table(_closed_period(B_events, cfg, "B", H)),
        "\n## Tutte le celle B (descrittive)\n", rp.summary_table(_cells_by_band(cb, cfg, "B")),
        "\n" + rp.FORMULAS,
    ]
    (config.BACKTEST_DIR / "11_backtest_B.md").write_text("\n".join(txt) + "\n", encoding="utf-8")

    # --- matched control e placebo ---
    pl = run.placebo(P_events, env, reg, quiet)
    decomposition = []
    ok = P_events[P_events[S].eq("OK")]
    for year, grp in ok.groupby(ok["event_day"].dt.year):
        pair = grp[grp["excess_vs_peer"].notna()]
        decomposition.append((str(year), len(grp), rp.pct(grp[H].mean()), len(pair), rp.pct(pair["excess_vs_peer"].mean()),
                              rp.pct((pair[H] - pair["excess_vs_peer"]).mean())))
    ctrl_cells = []
    for band in run.BANDS:
        ea = run.select(ca, band, cfg, "b")
        eb = run.select(cb, band, cfg, "b")
        ctrl_cells += [(f"A (b) {band} vs indice", run.cell(ea, H, cfg)), (f"A (b) {band} vs peer", run.cell(ea, "excess_vs_peer", cfg)),
                       (f"B (b) {band} vs indice", run.cell(eb, H, cfg)), (f"B (b) {band} vs peer", run.cell(eb, "excess_vs_peer", cfg))]
    txt = [
        "# 12 — Matched control\n",
        f"Generato {_now()}. Peer: stessa banda alla stessa data, nessuna riga B_row visibile nei 60 giorni prima, log-cap più vicino.\n",
        "## Esito della selezione del peer nella cella P\n",
        rp.counts_table(P_events.loc[P_events[S].eq("OK"), "peer_status"], "stato gamba peer"),
        "\n## Celle per banda\n", rp.summary_table(ctrl_cells),
        "\n## Scomposizione per anno (cella P)\n",
        "`eccesso vs indice` − `eccesso vs peer` = rendimento medio dei peer contro l'indice: la parte attribuibile alla dimensione.\n",
        __import__("fi_insider_scanner.mdtable", fromlist=["md_table"]).md_table(pd.DataFrame(decomposition, columns=["anno", "n P", "eccesso vs indice", "coppie", "eccesso vs peer", "peer vs indice"])),
        "\n## Placebo (date spostate di −252 sessioni, stessi emittenti)\n",
        rp.summary_table([("placebo vs indice", run.cell(pl, H, cfg)), ("placebo vs peer", run.cell(pl, "excess_vs_peer", cfg))]),
        "\nAtteso ≈ 0 contro il peer: un valore lontano da zero indica un bias della pipeline, non un segnale.\n",
        "\n" + rp.FORMULAS,
    ]
    (config.BACKTEST_DIR / "12_matched_control.md").write_text("\n".join(txt) + "\n", encoding="utf-8")

    # --- survivorship ---
    st = surv["table"].copy()
    rows = [(f"{r.ambito} · {r.scenario} (+{r.aggiunti})", __import__("fi_insider_scanner.backtest.stats", fromlist=["Summary"]).Summary(
        **{k: getattr(r, k) for k in ("n", "mean", "median", "sd", "share_positive", "t_iid", "t_cr1_issuer", "t_cr1_month", "t_two_way", "ci_low", "ci_high", "mde", "n_issuers", "n_months")}))
        for r in st.itertuples()]
    status_by_year = pd.crosstab(all_b["event_day"].dt.year.astype(str), all_b[S].fillna("(null)"))
    status_by_year.loc["totale"] = status_by_year.sum()
    ub = pd.DataFrame({"non risolti (banda ignota)": surv["unresolved_by_year"], "attesi in banda": surv["expected_by_year"]}).fillna(0).astype(int)
    txt = [
        "# 13 — Survivorship\n",
        f"Generato {_now()}.\n",
        "## Stato del rendimento per anno (A variante b, tutte le bande)\n",
        __import__("fi_insider_scanner.mdtable", fromlist=["md_table"]).md_table(status_by_year, index=True, digits=0),
        "\n## Eventi senza banda (ticker o mcap mancanti)\n",
        __import__("fi_insider_scanner.mdtable", fromlist=["md_table"]).md_table(ub.rename_axis("anno").reset_index().astype({"anno": str}), digits=0),
        f"\nNon risolti: **{surv['n_unresolved']:,}**; attesi in banda 50-300M: **{surv['expected_in_band']:,}**; "
        f"con indizio di acquisizione (vendite fuori mercato allo stesso prezzo prima dell'ultima riga): {surv['acquired_in_unresolved']:,}. "
        f"r̄_OMXSPI sugli eventi osservati: {rp.pct(surv['r_bench_mean'])}.\n",
        f"\nBreak-even p* (quota dei non risolti a −100% che azzera la media di P): sugli attesi in banda "
        f"{rp.pct(surv['break_even_expected'], sign=False)}, su tutti {rp.pct(surv['break_even_all'], sign=False)}.\n",
        "\n## P con gli scenari aggiunti\n", rp.summary_table([("P osservata", P)] + rows),
        "\nS_minus100 = −1 − r̄_bench; S_minus50 = −0,5 − r̄_bench; S0 = 0; S_plus = +15%; S_draw = estrazione dalla distribuzione osservata; "
        "S_mix_acquired = +15% se c'è indizio di acquisizione, altrimenti −100%.\n",
    ]
    (config.BACKTEST_DIR / "13_survivorship.md").write_text("\n".join(txt) + "\n", encoding="utf-8")

    # --- verdetto ---
    checks = pd.DataFrame([(k, str(v)) for k, v in verdict.checks.items()], columns=["criterio", "valore"])
    txt = [
        "# 20 — Verdetto pre-registrato\n",
        f"Generato {_now()}. Criteri: `backtest/preregistration.md`. Nessuna interpretazione oltre i criteri.\n",
        f"## Esito: **{verdict.label}**\n",
        "\n".join(f"- {r}" for r in verdict.reasons),
        "\n## Numeri usati\n",
        rp.summary_table([("P: A (b) 50-300M 126s vs OMXSPI", P), ("C: stessi eventi vs peer", C)]),
        f"\nMedia di P con scenario S0 sugli attesi in banda: {rp.pct(s0_mean)}. Copertura: {coverage:.1%}.\n",
        "\n## Controlli\n",
        __import__("fi_insider_scanner.mdtable", fromlist=["md_table"]).md_table(checks),
        "\n## Riferimento USA\n",
        "Scanner USA su Form 4, stessa definizione: +3,50% (t = 4,30, iid) a 126 giorni in banda $50-300M vs IWM; matched control +2,41% (t = 2,02).\n",
    ]
    (config.BACKTEST_DIR / "20_verdict.md").write_text("\n".join(txt) + "\n", encoding="utf-8")
    return {"verdict": verdict.label, "P": P.as_dict(), "C": C.as_dict(), "coverage": coverage, "B": PB.as_dict()}
