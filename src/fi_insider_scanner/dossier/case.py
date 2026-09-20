"""Case zero end to end: build the recent cluster triggers, apply the declared selection rule, write the dossier.

The backtest runs on the pinned snapshot; this step prefers the refreshed database, because upstream row
statuses go stale exactly in the most recent weeks (ADR-002).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .. import config, pipeline, store
from ..backtest import main as backtest_main
from ..backtest import run
from ..backtest.events import build_b_events
from ..canon.visibility import Register
from ..gates.openmarket import b_row
from ..ingest.refresh import REFRESHED_DB
from ..mdtable import md_table
from . import build as dossier

CANDIDATE_COLUMNS = [
    "issuer_name",
    "as_of",
    "anchor",
    "n_persons",
    "value_sek",
    "score",
    "is_stale",
    "symbol",
    "verified",
    "mcap_usd",
    "band",
    "dilution",
    "s3_in_window",
]


@dataclass(frozen=True)
class CaseZeroResult:
    source: str
    candidates_path: Path
    dossier_path: Path | None
    case: pd.Series | None
    in_band: bool


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")[:40]


def _shares_outstanding(env: run.Env, symbol: str, as_of: pd.Timestamp, lag_days: int) -> float | None:
    """Share count usable at T, with the publication lag, or None."""
    shares = env.market.shares(symbol)
    if shares is None or shares.empty:
        return None
    available = shares[shares.index <= pd.Timestamp(as_of) - pd.Timedelta(days=lag_days)]
    return float(available.iloc[-1]) if len(available) else None


def recent_triggers(cfg: dict, env: run.Env, register: Register) -> pd.DataFrame:
    """Column-B triggers with market cap, restricted to issuers active in the case-zero window."""
    events = build_b_events(register, cfg, env.market)
    events = run.attach_mcap(events, env, "anchor")
    events["gate_ok"] = events["score"].eq(4) & ~events["is_stale"]
    return events


def run_case_zero(cfg: dict, use_pinned: bool = False, log=print) -> CaseZeroResult:
    window = cfg["caso_zero"]
    database = None if use_pinned or not REFRESHED_DB.exists() else REFRESHED_DB
    source = "snapshot pinnato" if database is None else f"snapshot pinnato + refresh FI ({store.load_meta('refresh', database)['window']})"

    env = backtest_main.load_env(cfg, database)
    canonical = pipeline.canonical_with_values() if database is None else pipeline.canonical_from(database)
    since = pd.Timestamp(window["window_start"]) - pd.Timedelta(days=cfg["cluster"]["window_days"] + 5)
    active_issuers = set(canonical.loc[b_row(canonical) & (canonical["trade_date"] >= since), "issuer_key"])
    log(f"{source}; emittenti con acquisti on-venue dal {since.date()}: {len(active_issuers)}")

    register = Register(canonical[canonical["issuer_key"].isin(active_issuers)], store.load_rules(database))
    selection = dossier.select_case(recent_triggers(cfg, env, register), cfg)

    config.DOSSIER_DIR.mkdir(exist_ok=True)
    ranked = selection.candidates[CANDIDATE_COLUMNS].copy()
    ranked["mcap_usd"] = (ranked["mcap_usd"] / 1e6).round(0)
    candidates_path = config.DOSSIER_DIR / f"{window['window_end']}_candidati.md"
    candidates_path.write_text(
        f"# Candidati caso zero\n\nRegola: {selection.rule}.\n\nFonte: {source}.\n\n"
        + md_table(ranked.astype({"as_of": str, "anchor": str}))
        + "\n",
        encoding="utf-8",
    )
    if selection.case is None:
        return CaseZeroResult(source, candidates_path, None, None, False)

    case = selection.case
    symbol = case["symbol"]
    markdown = dossier.build_dossier(
        case,
        register,
        cfg,
        _shares_outstanding(env, symbol, case["as_of"], cfg["dilution"]["shares_lag_days"]),
        env.market.reports(symbol),
        dossier.load_sources(config.DOSSIER_DIR / f"{_slug(case['issuer_name'])}_sources.json"),
        selection.in_band,
        selection.rule,
        source,
    )
    dossier_path = config.DOSSIER_DIR / f"{window['window_end']}_{_slug(case['issuer_name'])}.md"
    dossier_path.write_text(markdown, encoding="utf-8")
    return CaseZeroResult(source, candidates_path, dossier_path, case, selection.in_band)
