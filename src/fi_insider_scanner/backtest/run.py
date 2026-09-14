"""Checkpoint 6-10: market cap e bande, rendimenti, matched control, survivorship, placebo.

Qui si usano anche informazioni successive agli eventi (rendimenti, colonne `expost_`): questo modulo
misura, non seleziona. La selezione degli eventi avviene in `events.py` con `Register.visible()`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..canon.visibility import Register
from ..market.context import YahooMarket
from ..market.mcap import band_label, mcap_at, mcap_panel
from . import survivorship as sv
from .control import QuietIndex, pick_peer
from .events import apply_cooldown, build_a_events, build_b_events
from .returns import event_return, monthly_excess
from .stats import Summary, calendar_time_t, summarize

BANDS = ("lt50", "50_300", "gt300")
WEAK_TYPE_SOURCES = {"isin_majority", "name_rule", "issuer_name_match"}
ISSUE_TYPES = {"bta", "btu", "subscription_right", "interim_share"}


def asof_values(series: pd.Series, dates) -> np.ndarray:
    idx = series.index.to_numpy()
    d = pd.to_datetime(pd.Series(dates)).dt.normalize().to_numpy()
    pos = idx.searchsorted(d, side="right") - 1
    out = np.full(len(d), np.nan)
    ok = pos >= 0
    out[ok] = series.to_numpy(dtype=float)[pos[ok]]
    return out


@dataclass
class Env:
    cfg: dict
    market: YahooMarket
    bench: pd.Series
    usdsek: pd.Series
    current: pd.DataFrame  # righe correnti del registro (diagnostica ex post, dual class, tipi)
    _type_source: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._type_source = dict(zip(self.current["record_id"], self.current["type_source"]))
        shares = self.current[self.current["instrument_type"].eq("share")]
        classes = shares.dropna(subset=["share_class"]).groupby("issuer_key")["share_class"].nunique()
        self.dual_class = set(classes[classes >= 2].index)


# --- market cap e bande ---------------------------------------------------------------------


def attach_mcap(events: pd.DataFrame, env: Env, date_col: str) -> pd.DataFrame:
    if events.empty:
        return events
    cfg = env.cfg
    lag = cfg["dilution"]["shares_lag_days"]
    low, high, edge = cfg["band"]["low_usd"], cfg["band"]["high_usd"], cfg["band"]["edge_sensitivity"]
    rows = []
    for issuer, isin, day in zip(events["issuer_key"], events["isin"], events[date_col]):
        sym = env.market.symbol_for_isin(isin)
        point = mcap_at(env.market.history(sym), env.market.shares(sym), day, lag) if sym else None
        rows.append(
            {
                "symbol": sym,
                "symbol_source": "isin" if sym else None,
                "verified": env.market.is_verified(isin) if sym else None,
                "mcap_reason": point.reason if point else "NO_SYMBOL",
                "mcap_sek": point.mcap_sek if point else None,
                "shares_used": point.shares if point else None,
                "shares_date": point.shares_date if point else None,
                "close_raw": point.close_raw if point else None,
            }
        )
    out = events.reset_index(drop=True).join(pd.DataFrame(rows))
    out["usdsek"] = asof_values(env.usdsek, out[date_col])
    out["mcap_usd"] = out["mcap_sek"].astype(float) / out["usdsek"]
    out["band"] = [band_label(v, low, high) for v in out["mcap_usd"]]
    out["in_band_narrow"] = (out["mcap_usd"] >= low * (1 + edge)) & (out["mcap_usd"] < high * (1 - edge))
    out["in_band_wide"] = (out["mcap_usd"] >= low * (1 - edge)) & (out["mcap_usd"] < high * (1 + edge))
    out["dual_class"] = out["issuer_key"].isin(env.dual_class)
    out["weak_type"] = out["record_ids"].map(lambda ids: any(env._type_source.get(r) in WEAK_TYPE_SOURCES for r in ids.split("|")))
    return out


# --- rendimenti -----------------------------------------------------------------------------


def attach_returns(events: pd.DataFrame, env: Env) -> pd.DataFrame:
    if events.empty:
        return events
    bt = env.cfg["backtest"]
    h_primary = bt["primary_horizon"]
    rows = []
    for sym, day in zip(events["symbol"], events["event_day"]):
        hist = env.market.history(sym) if isinstance(sym, str) else None
        rec: dict = {}
        for h in bt["horizons"]:
            r = event_return(hist, env.bench, day, h, bt["max_stale_sessions"], bt["artefact_abs_return"])
            rec[f"status_{h}"] = r.status if isinstance(sym, str) else "NO_SYMBOL"
            rec[f"excess_{h}"] = r.excess
            if h == h_primary:
                rec.update(
                    entry_date=r.entry_date, exit_date=r.exit_date, r_stock=r.r_stock, r_bench=r.r_bench,
                    excess_adj=r.excess_adj, excess_last_flat=r.excess_last_flat,
                    stale_entry_sessions=r.stale_entry_sessions, stale_exit_sessions=r.stale_exit_sessions,
                    expost_max_abs_daily=r.expost_max_abs_daily,
                )
                own = event_return(hist, env.bench, day, h, bt["max_stale_sessions"], bt["artefact_abs_return"], own_bars=True)
                rec["status_own_bars"] = own.status if isinstance(sym, str) else "NO_SYMBOL"
                rec["excess_own_bars"] = own.excess
        rows.append(rec)
    out = events.reset_index(drop=True).join(pd.DataFrame(rows))
    out["expost_large_move"] = out["expost_max_abs_daily"].astype(float) > bt["large_daily_move"]
    out["expost_rights_issue"] = expost_rights_issue(out, env)
    return out


def expost_rights_issue(events: pd.DataFrame, env: Env) -> pd.Series:
    cur = env.current
    issues = cur[cur["txn_kind"].eq("subscription") | cur["instrument_type"].isin(ISSUE_TYPES)]
    by_issuer = {k: g["trade_date"].sort_values().to_numpy() for k, g in issues.groupby("issuer_key")}
    flags = []
    for issuer, entry, exit_ in zip(events["issuer_key"], events["entry_date"], events["exit_date"]):
        arr = by_issuer.get(issuer)
        if arr is None or pd.isna(entry) or pd.isna(exit_):
            flags.append(False)
            continue
        lo = arr.searchsorted(np.datetime64(pd.Timestamp(entry)), side="right")
        hi = arr.searchsorted(np.datetime64(pd.Timestamp(exit_)), side="right")
        flags.append(bool(hi > lo))
    return pd.Series(flags, index=events.index)


# --- matched control ------------------------------------------------------------------------


class Pool:
    def __init__(self, env: Env, dates: pd.DatetimeIndex):
        lag = env.cfg["dilution"]["shares_lag_days"]
        self.symbols = env.market.issuer_symbols()
        dates = pd.DatetimeIndex(sorted(set(pd.DatetimeIndex(dates).normalize())))
        usd = asof_values(env.usdsek, dates)
        cols = {}
        for issuer, sym in self.symbols.items():
            cols[issuer] = mcap_panel(env.market.history(sym), env.market.shares(sym), dates, lag) / usd
        self.panel = pd.DataFrame(cols, index=dates)
        self.low, self.high = env.cfg["band"]["low_usd"], env.cfg["band"]["high_usd"]

    def at(self, day: pd.Timestamp) -> pd.DataFrame:
        vals = self.panel.loc[pd.Timestamp(day).normalize()]
        df = pd.DataFrame({"issuer_key": vals.index, "mcap_usd": vals.to_numpy()})
        df["symbol"] = df["issuer_key"].map(self.symbols)
        df["band"] = [band_label(v, self.low, self.high) for v in df["mcap_usd"]]
        return df


def attach_control(events: pd.DataFrame, env: Env, quiet: QuietIndex, pool: Pool, date_col: str) -> pd.DataFrame:
    if events.empty:
        return events
    bt = env.cfg["backtest"]
    h = bt["primary_horizon"]
    rows = []
    for issuer, day, as_of, mcap_date, mcap_usd, band, r_event, status in zip(
        events["issuer_key"], events["event_day"], events["as_of"], events[date_col], events["mcap_usd"], events["band"],
        events["r_stock"], events[f"status_{h}"],
    ):
        rec = {"peer_issuer": None, "peer_symbol": None, "peer_status": None, "excess_vs_peer": None}
        if band is not None and pd.notna(mcap_usd) and status == "OK":
            active = quiet.active_issuers(as_of, day, bt["quiet_days_control"])
            peer = pick_peer(issuer, float(mcap_usd), band, pool.at(mcap_date), active)
            if peer is not None:
                r = event_return(env.market.history(peer["symbol"]), env.bench, day, h, bt["max_stale_sessions"], bt["artefact_abs_return"])
                rec.update(peer_issuer=peer["issuer_key"], peer_symbol=peer["symbol"], peer_status=r.status)
                if r.status == "OK":
                    rec["excess_vs_peer"] = r_event - r.r_stock
        rows.append(rec)
    return events.reset_index(drop=True).join(pd.DataFrame(rows))


# --- celle e statistiche --------------------------------------------------------------------


def cell(df: pd.DataFrame, value_col: str, cfg: dict, status_col: str | None = None) -> Summary:
    bt = cfg["backtest"]
    status_col = status_col or f"status_{bt['primary_horizon']}"
    ok = df[df[status_col].eq("OK")] if status_col in df else df
    ok = ok[ok[value_col].notna()]
    months = ok["event_day"].dt.to_period("M").astype(str)
    return summarize(ok[value_col].astype(float), ok["issuer_key"], months, bt["bootstrap_draws"], bt["bootstrap_seed"], bt["min_clusters_for_cr1"])


def select(events: pd.DataFrame, band: str | None, cfg: dict, variant: str = "b", mask: pd.Series | None = None) -> pd.DataFrame:
    sel = events if mask is None else events[mask.reindex(events.index, fill_value=False)]
    if band is not None:
        sel = sel[sel["band"].eq(band)]
    if variant == "b":
        sel = apply_cooldown(sel, cfg["backtest"]["cooldown_calendar_days"])
    return sel


def calendar_time(events: pd.DataFrame, env: Env) -> tuple[float | None, int]:
    parts = []
    for sym, entry, exit_ in zip(events["symbol"], events["entry_date"], events["exit_date"]):
        hist = env.market.history(sym)
        if hist is None or pd.isna(entry) or pd.isna(exit_):
            continue
        parts.append(monthly_excess(hist, env.bench, entry, exit_))
    return calendar_time_t(pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["month", "excess"]))


# --- survivorship ---------------------------------------------------------------------------


def survivorship_table(gated_b: pd.DataFrame, primary_ok: pd.DataFrame, env: Env, band: str = "50_300") -> dict:
    """gated_b: eventi A dopo gate e variante (b) su tutte le bande; primary_ok: cella P in stato OK."""
    cfg = env.cfg
    h = cfg["backtest"]["primary_horizon"]
    unresolved = gated_b[gated_b["band"].isna()]
    known = gated_b[gated_b["band"].notna()]
    year = lambda d: d["event_day"].dt.year  # noqa: E731
    p_year = known.groupby(year(known))["band"].apply(lambda s: float((s == band).mean()))
    n_u_year = unresolved.groupby(year(unresolved)).size()
    expected = {y: int(round(p_year.get(y, float((known["band"] == band).mean()) if len(known) else 0.0) * n)) for y, n in n_u_year.items()}
    r_b = float(primary_ok["r_bench"].mean()) if len(primary_ok) else 0.0
    observed = primary_ok.assign(month=primary_ok["event_day"].dt.to_period("M").astype(str))[["excess_" + str(h), "issuer_key", "month"]]
    observed = observed.rename(columns={f"excess_{h}": "value"})
    seed = cfg["survivorship"]["seed"]
    bt = cfg["backtest"]
    results = []
    acquired = sv.acquired_likely(env.current, cfg["survivorship"]["acquired_lookback_days"])
    for scope in ("attesi_in_banda", "tutti"):
        if scope == "tutti":
            add_rows = unresolved
        else:
            parts = [unresolved[year(unresolved) == y].sort_values("event_day").head(k) for y, k in expected.items()]
            add_rows = pd.concat(parts) if parts else unresolved.iloc[:0]
        base = add_rows.assign(month=add_rows["event_day"].dt.to_period("M").astype(str))
        for name in sv.SCENARIOS + ("S_mix_acquired",):
            if name == "S_mix_acquired":
                vals = np.where(base["issuer_key"].isin(acquired), cfg["survivorship"]["s_plus_excess"], -1.0 - r_b)
            else:
                vals = sv.scenario_values(name, len(base), r_b, cfg["survivorship"]["s_plus_excess"], observed["value"].to_numpy(), seed)
            added = pd.DataFrame({"value": vals, "issuer_key": base["issuer_key"].to_numpy(), "month": base["month"].to_numpy()})
            s = sv.pooled(observed, added, "value", bt["bootstrap_draws"], bt["bootstrap_seed"], bt["min_clusters_for_cr1"])
            results.append({"ambito": scope, "scenario": name, "aggiunti": len(added), **s.as_dict()})
    mean_obs = float(observed["value"].mean()) if len(observed) else None
    return {
        "table": pd.DataFrame(results),
        "n_unresolved": len(unresolved),
        "expected_in_band": int(sum(expected.values())),
        "r_bench_mean": r_b,
        "break_even_all": sv.break_even_share(mean_obs, len(observed), len(unresolved), r_b) if mean_obs is not None else None,
        "break_even_expected": sv.break_even_share(mean_obs, len(observed), int(sum(expected.values())), r_b) if mean_obs is not None else None,
        "acquired_in_unresolved": int(unresolved["issuer_key"].isin(acquired).sum()),
        "unresolved_by_year": n_u_year,
        "expected_by_year": pd.Series(expected, dtype=int),
    }


# --- colonne complete -----------------------------------------------------------------------


def in_period(events: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    bt = cfg["backtest"]
    if events.empty:
        return events
    return events[(events["event_day"] >= pd.Timestamp(bt["start"])) & (events["event_day"] <= pd.Timestamp(bt["end"]))].reset_index(drop=True)


def column_a(register: Register, env: Env) -> pd.DataFrame:
    a = in_period(build_a_events(register, env.cfg, env.market), env.cfg)
    a = attach_mcap(a, env, "last_trade")
    a["gate_ok"] = a["dilution"].ne("BLOCKED")
    return attach_returns(a, env)


def column_b(register: Register, env: Env) -> pd.DataFrame:
    b = in_period(build_b_events(register, env.cfg, env.market), env.cfg)
    b = attach_mcap(b, env, "anchor")
    b["gate_ok"] = b["score"].eq(4) & ~b["is_stale"]
    return attach_returns(b, env)


def placebo(primary: pd.DataFrame, env: Env, register: Register, quiet: QuietIndex) -> pd.DataFrame:
    shift = env.cfg["backtest"]["placebo_shift_sessions"]
    sessions = env.bench.index
    rows = primary.copy()
    new_days = []
    for day in rows["event_day"]:
        i = int(sessions.searchsorted(day, side="left")) - shift
        new_days.append(sessions[i] if i >= 0 else pd.NaT)
    delta = pd.Series(new_days, index=rows.index) - rows["event_day"]
    rows["event_day"] = pd.to_datetime(pd.Series(new_days, index=rows.index))
    rows["as_of"] = rows["as_of"] + delta
    rows["last_trade"] = rows["last_trade"] + delta
    rows = rows.dropna(subset=["event_day"])
    keep = [c for c in ("issuer_key", "isin", "event_day", "as_of", "last_trade", "record_ids", "n_rows") if c in rows]
    rows = attach_mcap(rows[keep].reset_index(drop=True), env, "last_trade")
    rows = attach_returns(rows, env)
    rows = rows[rows["band"].eq("50_300")].reset_index(drop=True)
    pool = Pool(env, pd.DatetimeIndex(rows["last_trade"]))
    return attach_control(rows, env, quiet, pool, "last_trade")
