"""Orchestration of checkpoint 6 (gates + market cap), 6b (pre-registration) and 7-10 (returns,
matched control, survivorship, placebo, verdict).

This module computes; `report.py` renders. The order of the filters — gate, then band, then the
one-event-per-issuer cooldown — mirrors the US script, and is fixed by the pre-registration.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config, pipeline, store
from ..gates.closed_period import MAX_REPORT_GAP_DAYS
from ..market import fx as fxmod
from ..market import yf_cache
from ..market.context import YahooMarket
from . import prereg, run
from . import report as rp
from .control import QuietIndex
from .stats import Summary
from .verdict import decide

DATE_COLS = ("event_day", "as_of", "first_trade", "last_trade", "anchor", "window_end", "shares_date", "entry_date", "exit_date")
BOOL_COLS = (
    "has_onvenue_row",
    "all_natural",
    "dil_participation",
    "dil_trap",
    "gate_ok",
    "is_stale",
    "s3_in_window",
    "uniform_onvenue",
    "s1_subscription",
    "s2_issue_instruments",
    "not_routine",
    "dilution_ok",
    "no_large_holder",
    "in_band_narrow",
    "in_band_wide",
    "dual_class",
    "weak_type",
)
SUMMARY_FIELDS = (
    "n",
    "mean",
    "median",
    "sd",
    "share_positive",
    "t_iid",
    "t_cr1_issuer",
    "t_cr1_month",
    "t_two_way",
    "ci_low",
    "ci_high",
    "mde",
    "n_issuers",
    "n_months",
)


def load_env(cfg: dict, db_path=None) -> run.Env:
    """Market data plus the current register rows; `db_path` switches to the refreshed database."""
    df = pipeline.canonical_with_values() if db_path is None else pipeline.canonical_from(db_path)
    market = YahooMarket(store.load_frame("resolution"))
    bench = yf_cache.history(cfg["backtest"]["benchmark"])["Close"].astype(float)
    return run.Env(cfg, market, bench, fxmod.load_fx()["USD"], df[df["chain_status"].eq("current")].copy())


def load_events(name: str) -> pd.DataFrame:
    """Read an event table back from SQLite, restoring dates, booleans and the tri-state columns."""
    events = store.load_frame(name)
    for col in DATE_COLS:
        if col in events:
            events[col] = pd.to_datetime(events[col])
    for col in BOOL_COLS:
        if col in events:
            events[col] = events[col].map(lambda v: bool(v) if pd.notna(v) else False)
    if "verified" in events:
        events["verified"] = events["verified"].map(lambda v: None if pd.isna(v) else bool(v))
    if "band" in events:
        events["band"] = events["band"].map(lambda v: None if pd.isna(v) else str(v))
    return events


# --- checkpoint 6 and 6b -------------------------------------------------------------------------


def gates_mcap(cfg: dict) -> str:
    """Build both event columns with gates and market cap, and write report 05. No returns yet."""
    env = load_env(cfg)
    register = pipeline.register("snapshot", "pub")
    a, b = run.column_a(register, env), run.column_b(register, env)
    store.save_frame("events_a", a)
    store.save_frame("events_b", b)
    md = rp.gates_mcap_report(a, b, env.usdsek, cfg)
    (config.BACKTEST_DIR / "05_gates_mcap.md").write_text(md, encoding="utf-8")
    return md


def freeze(cfg: dict) -> str:
    """Write the pre-registration; it must be committed before any forward return is computed."""
    md = prereg.build(cfg)
    (config.BACKTEST_DIR / "preregistration.md").write_text(md, encoding="utf-8")
    return md


# --- cell builders --------------------------------------------------------------------------------


def _last_flat(events: pd.DataFrame, value: str, status: str) -> pd.DataFrame:
    """Delisted-in-window events kept at their last price, merged with the OK ones."""
    kept = events[events[status].isin(["OK", "ENDED_IN_WINDOW"])].copy()
    kept["v_last_flat"] = np.where(kept[status].eq("OK"), kept[value], kept["excess_last_flat"])
    kept["st_last_flat"] = "OK"
    return kept


def _cells_by_band(events: pd.DataFrame, cfg: dict, prefix: str) -> list[tuple[str, Summary]]:
    return [
        (
            f"{prefix} ({variant}) {band or 'tutte'} {horizon}s",
            run.cell(run.select(events, band, cfg, variant), f"excess_{horizon}", cfg, f"status_{horizon}"),
        )
        for band in (*run.BANDS, None)
        for variant in ("b", "a")
        for horizon in cfg["backtest"]["horizons"]
    ]


def _closed_period_cells(events: pd.DataFrame, cfg: dict, label: str, value: str) -> list[tuple[str, Summary]]:
    """Report lists older than 200 days are incomplete, so they count as UNKNOWN (ADR-043)."""
    days = events["days_since_report"].where(events["days_since_report"] <= MAX_REPORT_GAP_DAYS)
    rows = []
    for window in (cfg["closed_period"]["window_days_primary"], cfg["closed_period"]["window_days_descriptive"]):
        rows.append((f"{label}: dentro finestra post-report ≤ {window} gg", run.cell(events[days.notna() & (days <= window)], value, cfg)))
        rows.append((f"{label}: fuori finestra (> {window} gg)", run.cell(events[days.notna() & (days > window)], value, cfg)))
    rows.append((f"{label}: data report UNKNOWN", run.cell(events[days.isna()], value, cfg)))
    return rows


def _sensitivities(
    ca: pd.DataFrame, ungated: pd.DataFrame, primary_events: pd.DataFrame, primary: Summary, env: run.Env
) -> list[tuple[str, Summary]]:
    """Descriptive variants of the primary cell; none of them can change the verdict."""
    cfg = env.cfg
    horizon = cfg["backtest"]["primary_horizon"]
    value, status = f"excess_{horizon}", f"status_{horizon}"
    in_band = lambda frame: run.select(frame, "50_300", cfg, "b")  # noqa: E731 - local shorthand
    rows = [
        ("P primaria", primary),
        ("netto 100bp", run.cell(primary_events, "excess_net", cfg)),
        ("Adj Close (limite superiore)", run.cell(primary_events, "excess_adj", cfg)),
        ("parità di bar (uscita nella serie del titolo)", run.cell(primary_events, "excess_own_bars", cfg, "status_own_bars")),
        ("senza expost_rights_issue", run.cell(primary_events[~primary_events["expost_rights_issue"]], value, cfg)),
        ("senza expost_large_move", run.cell(primary_events[~primary_events["expost_large_move"]], value, cfg)),
        ("ENDED_IN_WINDOW all'ultimo prezzo", run.cell(_last_flat(primary_events, value, status), "v_last_flat", cfg, "st_last_flat")),
        ("A_onvenue", run.cell(in_band(ca[ca["has_onvenue_row"]]), value, cfg)),
        ("senza dilution gate", run.cell(in_band(ungated), value, cfg)),
        ("solo ticker verified=True", run.cell(in_band(ca[ca["verified"].eq(True)]), value, cfg)),
        ("senza emittenti dual class", run.cell(in_band(ca[~ca["dual_class"]]), value, cfg)),
        ("solo tipo strumento dichiarato/unanime", run.cell(in_band(ca[~ca["weak_type"]]), value, cfg)),
        ("banda con bordi stretti ±20%", run.cell(run.select(ca[ca["in_band_narrow"]], None, cfg, "b"), value, cfg)),
        ("banda con bordi larghi ±20%", run.cell(run.select(ca[ca["in_band_wide"]], None, cfg, "b"), value, cfg)),
    ]
    for mode, timing in (("as_seen", "pub"), ("snapshot", "first_pub")):
        alternative = run.attach_returns(run.column_a(pipeline.register(mode, timing), env), env)
        rows.append((f"visibilità {mode} + timing {timing}", run.cell(in_band(alternative[alternative["gate_ok"]]), value, cfg)))
    return rows


def _decomposition(ok_events: pd.DataFrame, value: str) -> list[tuple]:
    """Per year: excess against the index, against the peer, and the peers' own excess (the size part)."""
    rows = []
    for year, group in ok_events.groupby(ok_events["event_day"].dt.year):
        paired = group[group["excess_vs_peer"].notna()]
        rows.append(
            (
                str(year),
                len(group),
                rp.pct(group[value].mean()),
                len(paired),
                rp.pct(paired["excess_vs_peer"].mean()),
                rp.pct((paired[value] - paired["excess_vs_peer"]).mean()),
            )
        )
    return rows


def _scenario_cells(table: pd.DataFrame) -> list[tuple[str, Summary]]:
    return [
        (f"{row.scope} · {row.scenario} (+{row.added})", Summary(**{f: getattr(row, f) for f in SUMMARY_FIELDS}))
        for row in table.itertuples()
    ]


# --- checkpoints 7-10 -------------------------------------------------------------------------------


def backtest(cfg: dict) -> dict:
    """Returns, matched control, survivorship, placebo and the pre-registered verdict."""
    bt = cfg["backtest"]
    horizon = bt["primary_horizon"]
    value, status = f"excess_{horizon}", f"status_{horizon}"
    env = load_env(cfg)
    register = pipeline.register("snapshot", "pub")

    a = run.attach_returns(load_events("events_a"), env)
    b = run.attach_returns(load_events("events_b"), env)
    for events in (a, b):
        events["excess_net"] = events[value] - bt["cost_bps"] / 10_000
    gated_a, gated_b = a[a["gate_ok"]], b[b["gate_ok"]]

    quiet = QuietIndex(register)
    dates = pd.DatetimeIndex(
        pd.concat([gated_a.loc[gated_a["band"].notna(), "last_trade"], gated_b.loc[gated_b["band"].notna(), "anchor"]])
    )
    pool = run.Pool(env, dates)
    ca = run.attach_control(gated_a, env, quiet, pool, "last_trade")
    cb = run.attach_control(gated_b, env, quiet, pool, "anchor")
    ca.to_csv(config.BACKTEST_DIR / "10_events_A.csv", index=False)
    cb.to_csv(config.BACKTEST_DIR / "11_events_B.csv", index=False)

    # --- column A: the primary cell and its control ---
    primary_events = run.select(ca, "50_300", cfg, "b")
    primary = run.cell(primary_events, value, cfg)
    control = run.cell(primary_events, "excess_vs_peer", cfg)
    primary_ok = primary_events[primary_events[status].eq("OK")]
    all_bands = run.select(ca, None, cfg, "b")
    coverage = float(all_bands[status].eq("OK").mean()) if len(all_bands) else 0.0

    surv = run.survivorship_table(all_bands, primary_ok, env)
    s0 = surv["table"].query("scope == 'attesi_in_banda' and scenario == 'S0'")["mean"]
    s0_mean = float(s0.iloc[0]) if len(s0) and pd.notna(s0.iloc[0]) else None
    verdict = decide(primary, control, s0_mean, coverage, bt["min_coverage_for_verdict"])

    sensitivities = _sensitivities(ca, a, primary_events, primary, env)
    closed_a = _closed_period_cells(primary_events, cfg, "P", value)
    funnel_a = [
        ("eventi A nel periodo (variante a)", len(a)),
        ("dopo dilution gate", len(gated_a)),
        ("con ticker del proprio ISIN (verified ≠ False)", int(gated_a["symbol"].notna().sum())),
        ("con market cap", int(gated_a["mcap_usd"].notna().sum())),
        ("in banda 50-300M", int(gated_a["band"].eq("50_300").sum())),
        ("variante (b)", len(primary_events)),
        (f"rendimento OK a {horizon} sessioni", len(primary_ok)),
    ]
    (config.BACKTEST_DIR / "10_backtest_A.md").write_text(
        rp.column_a_report(
            funnel=funnel_a,
            status_counts=primary_events[status],
            primary=primary,
            control=control,
            calendar=run.calendar_time(primary_ok, env),
            coverage=coverage,
            per_year=rp.per_year_table(primary_events, value, status),
            sensitivities=sensitivities,
            closed_period=closed_a,
            cells=_cells_by_band(ca, cfg, "A"),
            horizon=horizon,
        ),
        encoding="utf-8",
    )

    # --- column B: the prompt's cluster version, descriptive ---
    b_events = run.select(cb, "50_300", cfg, "b")
    b_primary = run.cell(b_events, value, cfg)
    non_stale = b[~b["is_stale"]]
    b_cells = [
        ("B primaria: 4/4 non stale (b) 50-300M", b_primary),
        ("C: stessi eventi vs peer", run.cell(b_events, "excess_vs_peer", cfg)),
        ("senza acquisti simbolici", run.cell(run.select(cb[cb["n_symbolic"].eq(0)], "50_300", cfg, "b"), value, cfg)),
        ("score ≥ 3 non stale", run.cell(run.select(non_stale[non_stale["score"] >= 3], "50_300", cfg, "b"), value, cfg)),
        ("senza expost_rights_issue", run.cell(b_events[~b_events["expost_rights_issue"]], value, cfg)),
        ("Adj Close (limite superiore)", run.cell(b_events, "excess_adj", cfg)),
        ("netto 100bp", run.cell(b_events, "excess_net", cfg)),
    ] + [
        (
            f"score {score} non stale (b) 50-300M",
            run.cell(run.select(non_stale[non_stale["score"].eq(score)], "50_300", cfg, "b"), value, cfg),
        )
        for score in (4, 3, 2, 1, 0)
    ]
    funnel_b = [
        ("trigger B nel periodo", len(b)),
        ("non stale", len(non_stale)),
        ("4/4 non stale", len(gated_b)),
        ("con ticker del proprio ISIN", int(gated_b["symbol"].notna().sum())),
        ("in banda 50-300M", int(gated_b["band"].eq("50_300").sum())),
        ("variante (b)", len(b_events)),
        (f"rendimento OK a {horizon} sessioni", int(b_events[status].eq("OK").sum())),
    ]
    (config.BACKTEST_DIR / "11_backtest_B.md").write_text(
        rp.column_b_report(
            funnel=funnel_b,
            cells_main=b_cells,
            calendar=run.calendar_time(b_events[b_events[status].eq("OK")], env),
            per_year=rp.per_year_table(b_events, value, status),
            closed_period=_closed_period_cells(b_events, cfg, "B", value),
            cells=_cells_by_band(cb, cfg, "B"),
            horizon=horizon,
        ),
        encoding="utf-8",
    )

    # --- matched control and placebo ---
    placebo = run.placebo(primary_events, env, register, quiet)
    placebo_cells = [("placebo vs indice", run.cell(placebo, value, cfg)), ("placebo vs peer", run.cell(placebo, "excess_vs_peer", cfg))]
    band_cells = []
    for band in run.BANDS:
        events_a, events_b = run.select(ca, band, cfg, "b"), run.select(cb, band, cfg, "b")
        band_cells += [
            (f"A (b) {band} vs indice", run.cell(events_a, value, cfg)),
            (f"A (b) {band} vs peer", run.cell(events_a, "excess_vs_peer", cfg)),
            (f"B (b) {band} vs indice", run.cell(events_b, value, cfg)),
            (f"B (b) {band} vs peer", run.cell(events_b, "excess_vs_peer", cfg)),
        ]
    (config.BACKTEST_DIR / "12_matched_control.md").write_text(
        rp.control_report(
            peer_status=primary_ok["peer_status"],
            band_cells=band_cells,
            decomposition=_decomposition(primary_ok, value),
            placebo_cells=placebo_cells,
        ),
        encoding="utf-8",
    )

    # --- survivorship ---
    status_by_year = pd.crosstab(all_bands["event_day"].dt.year.astype(str), all_bands[status].fillna("(null)"))
    status_by_year.loc["totale"] = status_by_year.sum()
    unresolved_by_year = (
        pd.DataFrame({"non risolti (banda ignota)": surv["unresolved_by_year"], "attesi in banda": surv["expected_by_year"]})
        .fillna(0)
        .astype(int)
    )
    (config.BACKTEST_DIR / "13_survivorship.md").write_text(
        rp.survivorship_report(
            status_by_year=status_by_year,
            unresolved_by_year=unresolved_by_year,
            surv=surv,
            primary=primary,
            scenario_cells=_scenario_cells(surv["table"]),
        ),
        encoding="utf-8",
    )

    # --- verdict ---
    known_report_date = primary_events["days_since_report"].where(primary_events["days_since_report"] <= MAX_REPORT_GAP_DAYS).notna()
    (config.BACKTEST_DIR / "20_verdict.md").write_text(
        rp.verdict_report(
            verdict=verdict,
            primary=primary,
            control=control,
            s0_mean=s0_mean,
            coverage=coverage,
            placebo_cells=placebo_cells,
            closed_period=closed_a,
            band_cells=band_cells,
            b_cells=b_cells,
            sensitivities=sensitivities,
            surv=surv,
            dilution_unknown_share=float(a["dilution"].eq("UNKNOWN").mean()),
            report_known_share=float(known_report_date.mean()),
        ),
        encoding="utf-8",
    )
    return {"verdict": verdict.label, "P": primary.as_dict(), "C": control.as_dict(), "coverage": coverage, "B": b_primary.as_dict()}
