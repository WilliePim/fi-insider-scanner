"""Checkpoints 6-10: market cap and bands, returns, matched control, survivorship, placebo.

This module also reads information published after an event (returns, `expost_` columns): it measures,
it does not select. Event selection lives in `events.py` and goes through `Register.visible()`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ..canon.visibility import Register
from ..market.context import YahooMarket
from ..market.mcap import band_label, mcap_at, mcap_panel
from . import survivorship as sv
from .control import PeerCandidates, QuietIndex, pick_peer
from .events import apply_cooldown, build_a_events, build_b_events
from .returns import event_return, monthly_excess
from .stats import Summary, calendar_time_t, summarize

BANDS = ("lt50", "50_300", "gt300")
WEAK_TYPE_SOURCES = frozenset({"isin_majority", "name_rule", "issuer_name_match"})
ISSUE_TYPES = frozenset({"bta", "btu", "subscription_right", "interim_share"})
OFF_VENUE = frozenset({"off_venue", "unknown"})


def asof_values(series: pd.Series, dates) -> np.ndarray:
    """Last value of `series` on or before each date; NaN before the first observation."""
    idx = series.index.to_numpy()
    days = pd.to_datetime(pd.Series(dates)).dt.normalize().to_numpy()
    pos = idx.searchsorted(days, side="right") - 1
    out = np.full(len(days), np.nan)
    ok = pos >= 0
    out[ok] = series.to_numpy(dtype=float)[pos[ok]]
    return out


@dataclass
class Env:
    """Everything the measurement steps read: config, market data and the current register rows."""

    cfg: dict
    market: YahooMarket
    bench: pd.Series
    usdsek: pd.Series
    current: pd.DataFrame
    type_source: dict[str, str] = field(default_factory=dict, init=False)
    dual_class: set[str] = field(default_factory=set, init=False)

    def __post_init__(self) -> None:
        cur = self.current
        self.type_source = dict(zip(cur["record_id"], cur["type_source"], strict=True))
        # record_id -> execution price and its context, so per-event lookups cost a dict hit
        self._row_by_id = {
            rid: (price, currency, venue, isin)
            for rid, price, currency, venue, isin in zip(
                cur["record_id"], cur["price"], cur["currency"], cur["venue_class"], cur["isin"], strict=True
            )
        }
        shares = cur[cur["instrument_type"].eq("share")]
        classes = shares.dropna(subset=["share_class"]).groupby("issuer_key")["share_class"].nunique()
        self.dual_class = set(classes[classes >= 2].index)

    def register_price(self, record_ids: str, isin) -> tuple[float | None, str | None]:
        """Execution price in SEK of the event rows on that ISIN: median on-venue, else off-venue."""
        on_venue, off_venue = [], []
        for rid in record_ids.split("|"):
            row = self._row_by_id.get(rid)
            if row is None:
                continue
            price, currency, venue, row_isin = row
            if currency != "SEK" or not price > 0 or (isin is not None and row_isin != isin):
                continue
            (off_venue if venue in OFF_VENUE else on_venue).append(price)
        if on_venue:
            return float(np.median(on_venue)), "register_onvenue"
        if off_venue:
            return float(np.median(off_venue)), "register_offvenue"
        return None, None

    def weak_type(self, record_ids: str) -> bool:
        return any(self.type_source.get(rid) in WEAK_TYPE_SOURCES for rid in record_ids.split("|"))


# --- market cap and bands --------------------------------------------------------------------


def attach_mcap(events: pd.DataFrame, env: Env, date_col: str) -> pd.DataFrame:
    """Add ticker, market cap at `date_col`, band and the band-edge sensitivities."""
    if events.empty:
        return events
    cfg = env.cfg
    lag = cfg["dilution"]["shares_lag_days"]
    low, high, edge = cfg["band"]["low_usd"], cfg["band"]["high_usd"], cfg["band"]["edge_sensitivity"]
    rows = []
    for isin, day, record_ids in zip(events["isin"], events[date_col], events["record_ids"], strict=True):
        symbol = env.market.symbol_for_isin(isin)
        price, source = env.register_price(record_ids, isin)
        point = (
            mcap_at(
                env.market.history(symbol),
                env.market.shares(symbol),
                day,
                lag,
                price,
                source,
                env.market.segments(symbol),
                env.market.splits(symbol),
            )
            if symbol
            else None
        )
        rows.append(
            {
                "symbol": symbol,
                "symbol_source": "isin" if symbol else None,
                "verified": env.market.is_verified(isin) if symbol else None,
                "mcap_reason": point.reason if point else "NO_SYMBOL",
                "mcap_sek": point.mcap_sek if point else None,
                "shares_used": point.shares if point else None,
                "shares_date": point.shares_date if point else None,
                "price_used": point.price_used if point else None,
                "price_source": point.price_source if point else None,
                "close_raw_yahoo": point.close_raw_yahoo if point else None,
            }
        )
    out = events.reset_index(drop=True).join(pd.DataFrame(rows))
    out["usdsek"] = asof_values(env.usdsek, out[date_col])
    out["mcap_usd"] = out["mcap_sek"].astype(float) / out["usdsek"]
    out["band"] = [band_label(v, low, high) for v in out["mcap_usd"]]
    out["in_band_narrow"] = (out["mcap_usd"] >= low * (1 + edge)) & (out["mcap_usd"] < high * (1 - edge))
    out["in_band_wide"] = (out["mcap_usd"] >= low * (1 - edge)) & (out["mcap_usd"] < high * (1 + edge))
    out["dual_class"] = out["issuer_key"].isin(env.dual_class)
    out["weak_type"] = out["record_ids"].map(env.weak_type)
    return out


# --- returns ----------------------------------------------------------------------------------


def attach_returns(events: pd.DataFrame, env: Env) -> pd.DataFrame:
    """Add one return per horizon, plus the primary-horizon diagnostics and `expost_` strata."""
    if events.empty:
        return events
    bt = env.cfg["backtest"]
    primary = bt["primary_horizon"]
    stale, artefact = bt["max_stale_sessions"], bt["artefact_abs_return"]
    rows = []
    for symbol, day in zip(events["symbol"], events["event_day"], strict=True):
        history = env.market.history(symbol) if isinstance(symbol, str) else None
        record: dict = {}
        for horizon in bt["horizons"]:
            r = event_return(history, env.bench, day, horizon, stale, artefact)
            record[f"status_{horizon}"] = r.status if isinstance(symbol, str) else "NO_SYMBOL"
            record[f"excess_{horizon}"] = r.excess
            if horizon != primary:
                continue
            record.update(
                entry_date=r.entry_date,
                exit_date=r.exit_date,
                r_stock=r.r_stock,
                r_bench=r.r_bench,
                excess_adj=r.excess_adj,
                excess_last_flat=r.excess_last_flat,
                stale_entry_sessions=r.stale_entry_sessions,
                stale_exit_sessions=r.stale_exit_sessions,
                expost_max_abs_daily=r.expost_max_abs_daily,
            )
            own = event_return(history, env.bench, day, horizon, stale, artefact, own_bars=True)
            record["status_own_bars"] = own.status if isinstance(symbol, str) else "NO_SYMBOL"
            record["excess_own_bars"] = own.excess
        rows.append(record)
    out = events.reset_index(drop=True).join(pd.DataFrame(rows))
    out["expost_large_move"] = out["expost_max_abs_daily"].astype(float) > bt["large_daily_move"]
    out["expost_rights_issue"] = expost_rights_issue(out, env)
    return out


def expost_rights_issue(events: pd.DataFrame, env: Env) -> pd.Series:
    """Diagnostic stratum: the issuer ran a subscription or issue instrument inside the holding window."""
    issues = env.current[env.current["txn_kind"].eq("subscription") | env.current["instrument_type"].isin(ISSUE_TYPES)]
    by_issuer = {k: g["trade_date"].sort_values().to_numpy() for k, g in issues.groupby("issuer_key")}
    flags = []
    for issuer, entry, exit_ in zip(events["issuer_key"], events["entry_date"], events["exit_date"], strict=True):
        dates = by_issuer.get(issuer)
        if dates is None or pd.isna(entry) or pd.isna(exit_):
            flags.append(False)
            continue
        after_entry = dates.searchsorted(np.datetime64(pd.Timestamp(entry)), side="right")
        upto_exit = dates.searchsorted(np.datetime64(pd.Timestamp(exit_)), side="right")
        flags.append(bool(upto_exit > after_entry))
    return pd.Series(flags, index=events.index)


# --- matched control ----------------------------------------------------------------------------


class Pool:
    """Market cap in USD of every issuer with a usable ticker, on the dates the events need.

    Bands are labelled once for the whole panel; `candidates_at` then returns numpy views.
    """

    def __init__(self, env: Env, dates: pd.DatetimeIndex):
        lag = env.cfg["dilution"]["shares_lag_days"]
        low, high = env.cfg["band"]["low_usd"], env.cfg["band"]["high_usd"]
        symbols = env.market.issuer_symbols()
        self.issuer_key = np.array(list(symbols), dtype=object)
        self.symbol = np.array([symbols[i] for i in self.issuer_key], dtype=object)
        self.dates = pd.DatetimeIndex(sorted(set(pd.DatetimeIndex(dates).normalize())))
        usd = asof_values(env.usdsek, self.dates)
        panel = np.empty((len(self.dates), len(self.issuer_key)))
        for col, issuer in enumerate(self.issuer_key):
            symbol = symbols[issuer]
            panel[:, col] = (
                mcap_panel(env.market.history(symbol), env.market.shares(symbol), self.dates, lag, env.market.segments(symbol)) / usd
            )
        self.values = panel
        self.bands = np.array([[band_label(v, low, high) for v in row] for row in panel], dtype=object)
        self._row_of_date = {date: i for i, date in enumerate(self.dates)}

    @property
    def shape(self) -> tuple[int, int]:
        return self.values.shape

    def candidates_at(self, day: pd.Timestamp) -> PeerCandidates:
        row = self._row_of_date[pd.Timestamp(day).normalize()]
        return PeerCandidates(self.issuer_key, self.symbol, self.values[row], self.bands[row])


def attach_control(events: pd.DataFrame, env: Env, quiet: QuietIndex, pool: Pool, date_col: str) -> pd.DataFrame:
    """Add the matched peer and the excess against it, for events with a band and an OK return."""
    if events.empty:
        return events
    bt = env.cfg["backtest"]
    horizon = bt["primary_horizon"]
    status_col = f"status_{horizon}"
    rows = []
    for issuer, day, as_of, mcap_date, mcap_usd, band, r_event, status in zip(
        events["issuer_key"],
        events["event_day"],
        events["as_of"],
        events[date_col],
        events["mcap_usd"],
        events["band"],
        events["r_stock"],
        events[status_col],
        strict=True,
    ):
        record = {"peer_issuer": None, "peer_symbol": None, "peer_status": None, "excess_vs_peer": None}
        if band is not None and pd.notna(mcap_usd) and status == "OK":
            active = quiet.active_issuers(as_of, day, bt["quiet_days_control"])
            peer = pick_peer(issuer, float(mcap_usd), band, pool.candidates_at(mcap_date), active)
            if peer is not None:
                r = event_return(
                    env.market.history(peer.symbol), env.bench, day, horizon, bt["max_stale_sessions"], bt["artefact_abs_return"]
                )
                record.update(peer_issuer=peer.issuer_key, peer_symbol=peer.symbol, peer_status=r.status)
                if r.status == "OK":
                    record["excess_vs_peer"] = r_event - r.r_stock
        rows.append(record)
    return events.reset_index(drop=True).join(pd.DataFrame(rows))


# --- cells and statistics -------------------------------------------------------------------------


def cell(df: pd.DataFrame, value_col: str, cfg: dict, status_col: str | None = None) -> Summary:
    """Summary of one result cell: the OK events of `df` measured on `value_col`."""
    bt = cfg["backtest"]
    status_col = status_col or f"status_{bt['primary_horizon']}"
    ok = df[df[status_col].eq("OK")] if status_col in df else df
    ok = ok[ok[value_col].notna()]
    months = ok["event_day"].dt.to_period("M").astype(str)
    return summarize(
        ok[value_col].astype(float), ok["issuer_key"], months, bt["bootstrap_draws"], bt["bootstrap_seed"], bt["min_clusters_for_cr1"]
    )


def select(events: pd.DataFrame, band: str | None, cfg: dict, variant: str = "b", mask: pd.Series | None = None) -> pd.DataFrame:
    """Filter order of the US test: gate (already applied) -> band -> variant (b) cooldown."""
    sel = events if mask is None else events[mask.reindex(events.index, fill_value=False)]
    if band is not None:
        sel = sel[sel["band"].eq(band)]
    if variant == "b":
        sel = apply_cooldown(sel, cfg["backtest"]["cooldown_calendar_days"])
    return sel


def calendar_time(events: pd.DataFrame, env: Env) -> tuple[float | None, int]:
    """Equal-weight monthly portfolio of the events' holding periods, and its t."""
    parts = []
    for symbol, entry, exit_ in zip(events["symbol"], events["entry_date"], events["exit_date"], strict=True):
        history = env.market.history(symbol)
        if history is None or pd.isna(entry) or pd.isna(exit_):
            continue
        parts.append(monthly_excess(history, env.bench, entry, exit_))
    return calendar_time_t(pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["month", "excess"]))


# --- survivorship ----------------------------------------------------------------------------------

SCOPE_LABELS = {"expected_in_band": "attesi_in_banda", "all": "tutti"}


def survivorship_table(gated_b: pd.DataFrame, primary_ok: pd.DataFrame, env: Env, band: str = "50_300") -> dict:
    """Scenarios for the events without a band, added to the observed primary cell.

    `gated_b`: column A after the gate and variant (b), every band. `primary_ok`: cell P, status OK.
    """
    cfg = env.cfg
    bt, surv_cfg = cfg["backtest"], cfg["survivorship"]
    horizon = bt["primary_horizon"]
    unresolved = gated_b[gated_b["band"].isna()]
    known = gated_b[gated_b["band"].notna()]
    fallback_share = float((known["band"] == band).mean()) if len(known) else 0.0
    share_by_year = known.groupby(known["event_day"].dt.year)["band"].apply(lambda s: float((s == band).mean()))
    unresolved_by_year = unresolved.groupby(unresolved["event_day"].dt.year).size()
    expected = {year: round(share_by_year.get(year, fallback_share) * n) for year, n in unresolved_by_year.items()}

    bench_mean = float(primary_ok["r_bench"].mean()) if len(primary_ok) else 0.0
    observed = primary_ok.assign(month=primary_ok["event_day"].dt.to_period("M").astype(str)).rename(
        columns={f"excess_{horizon}": "value"}
    )[["value", "issuer_key", "month"]]
    acquired = sv.acquired_likely(env.current, surv_cfg["acquired_lookback_days"])

    results = []
    for scope, label in SCOPE_LABELS.items():
        if scope == "all":
            added_rows = unresolved
        else:
            per_year = [unresolved[unresolved["event_day"].dt.year == y].sort_values("event_day").head(k) for y, k in expected.items()]
            added_rows = pd.concat(per_year) if per_year else unresolved.iloc[:0]
        months = added_rows["event_day"].dt.to_period("M").astype(str)
        for scenario in (*sv.SCENARIOS, "S_mix_acquired"):
            if scenario == "S_mix_acquired":
                values = np.where(added_rows["issuer_key"].isin(acquired), surv_cfg["s_plus_excess"], -1.0 - bench_mean)
            else:
                values = sv.scenario_values(
                    scenario, len(added_rows), bench_mean, surv_cfg["s_plus_excess"], observed["value"].to_numpy(), surv_cfg["seed"]
                )
            added = pd.DataFrame({"value": values, "issuer_key": added_rows["issuer_key"].to_numpy(), "month": months.to_numpy()})
            pooled = sv.pooled(observed, added, "value", bt["bootstrap_draws"], bt["bootstrap_seed"], bt["min_clusters_for_cr1"])
            results.append({"scope": label, "scenario": scenario, "added": len(added), **pooled.as_dict()})

    mean_observed = float(observed["value"].mean()) if len(observed) else None
    expected_total = int(sum(expected.values()))
    return {
        "table": pd.DataFrame(results),
        "n_unresolved": len(unresolved),
        "n_events": len(gated_b),
        "expected_in_band": expected_total,
        "r_bench_mean": bench_mean,
        "break_even_all": sv.break_even_share(mean_observed, len(observed), len(unresolved), bench_mean),
        "break_even_expected": sv.break_even_share(mean_observed, len(observed), expected_total, bench_mean),
        "acquired_in_unresolved": int(unresolved["issuer_key"].isin(acquired).sum()),
        "unresolved_by_year": unresolved_by_year,
        "expected_by_year": pd.Series(expected, dtype=int),
    }


# --- whole columns -----------------------------------------------------------------------------------


def in_period(events: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    bt = cfg["backtest"]
    if events.empty:
        return events
    inside = events["event_day"].between(pd.Timestamp(bt["start"]), pd.Timestamp(bt["end"]))
    return events[inside].reset_index(drop=True)


def column_a(register: Register, env: Env) -> pd.DataFrame:
    """Column A events with gate and market cap. No returns: those come after pre-registration."""
    events = in_period(build_a_events(register, env.cfg, env.market), env.cfg)
    events = attach_mcap(events, env, "last_trade")
    events["gate_ok"] = events["dilution"].ne("BLOCKED")
    return events


def column_b(register: Register, env: Env) -> pd.DataFrame:
    """Column B cluster triggers with market cap; the gate is score 4/4 and not stale."""
    events = in_period(build_b_events(register, env.cfg, env.market), env.cfg)
    events = attach_mcap(events, env, "anchor")
    events["gate_ok"] = events["score"].eq(4) & ~events["is_stale"]
    return events


def placebo(primary: pd.DataFrame, env: Env, register: Register, quiet: QuietIndex) -> pd.DataFrame:
    """Same issuers, event dates shifted back by N sessions: a pipeline-bias detector."""
    shift = env.cfg["backtest"]["placebo_shift_sessions"]
    sessions = env.bench.index
    rows = primary.copy()
    shifted = [sessions[i - shift] if (i := int(sessions.searchsorted(day, side="left"))) >= shift else pd.NaT for day in rows["event_day"]]
    shifted = pd.to_datetime(pd.Series(shifted, index=rows.index))
    delta = shifted - rows["event_day"]
    rows["event_day"], rows["as_of"], rows["last_trade"] = shifted, rows["as_of"] + delta, rows["last_trade"] + delta
    rows = rows.dropna(subset=["event_day"])
    keep = [c for c in ("issuer_key", "isin", "event_day", "as_of", "last_trade", "record_ids", "n_rows") if c in rows]
    rows = attach_returns(attach_mcap(rows[keep].reset_index(drop=True), env, "last_trade"), env)
    rows = rows[rows["band"].eq("50_300")].reset_index(drop=True)
    return attach_control(rows, env, quiet, Pool(env, pd.DatetimeIndex(rows["last_trade"])), "last_trade")
