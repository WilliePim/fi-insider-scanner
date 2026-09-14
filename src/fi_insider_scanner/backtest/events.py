"""Eventi A (analogo USA) e B (cluster Layer 1), valutati solo con `Register.visible()`.

A: (emittente, giorno di pubblicazione) con >= 1 riga A_exact visibile; gate = dilution != BLOCKED.
B: trigger cluster; gate Layer 1 valutati una volta a T.
Il contesto di mercato (azioni, split, date report) è opzionale: senza, la crescita azioni e la
soglia 10% del grande azionista restano sconosciute (dry-run del checkpoint 3).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from ..canon.visibility import Register
from ..gates.closed_period import days_since_report
from ..gates.clusters import detect_clusters
from ..gates.dilution import dilution_verdict
from ..gates.large_holder import large_holder, symbolic_purchase
from ..gates.openmarket import a_exact, a_onvenue
from ..gates.routine import routine_metrics
from ..gates.score import Layer1
from ..gates.structural import context_flags


@dataclass(frozen=True)
class MarketContext:
    shares: pd.Series | None = None
    splits: pd.Series | None = None
    report_dates: pd.DatetimeIndex | None = None

    def shares_asof(self, as_of: pd.Timestamp, lag_days: int) -> float | None:
        if self.shares is None or self.shares.empty:
            return None
        avail = self.shares[self.shares.index <= as_of.normalize() - pd.Timedelta(days=lag_days)]
        return None if avail.empty else float(avail.iloc[-1])


NO_MARKET = MarketContext()
MarketLookup = Callable[[str, str | None], MarketContext]


def _no_market(issuer_key: str, isin: str | None) -> MarketContext:
    return NO_MARKET


def _mode(s: pd.Series):
    s = s.dropna()
    return None if s.empty else s.mode().iat[0]


def build_a_events(register: Register, cfg: dict, market: MarketLookup = _no_market) -> pd.DataFrame:
    min_usd = cfg["openmarket"]["min_usd_per_row"]
    dc = cfg["dilution"]
    tl = register.timeline()
    cand = tl[a_exact(tl, min_usd)]
    cand = cand.assign(pub_day=cand["visible_from"].dt.normalize())
    rows_out = []
    for (issuer, day), grp in cand.groupby(["issuer_key", "pub_day"], sort=False):
        as_of = grp["visible_from"].max()
        v = register.visible(as_of, issuer)
        rows = v[a_exact(v, min_usd) & v["visible_from"].dt.normalize().eq(day)]
        if rows.empty:
            continue
        isin = _mode(rows["isin"])
        ctx = market(issuer, isin)
        last_buy = rows["trade_date"].max()
        dil = dilution_verdict(v, last_buy, as_of, dc, ctx.shares, ctx.splits)
        rows_out.append(
            {
                "issuer_key": issuer,
                "event_day": day,
                "as_of": as_of,
                "isin": isin,
                "issuer_name": _mode(rows["issuer_name_raw"]) if "issuer_name_raw" in rows else None,
                "n_rows": len(rows),
                "n_persons": rows["person_key"].nunique(),
                "value_usd": float(rows["value_usd"].sum()),
                "value_sek": float(rows["value_sek"].sum()),
                "first_trade": rows["trade_date"].min(),
                "last_trade": last_buy,
                "has_onvenue_row": bool(a_onvenue(rows, min_usd).any()),
                "all_natural": bool(rows["pdmr_is_natural_person"].eq(True).all()),
                "dilution": dil.verdict,
                "dil_participation": dil.participation,
                "dil_trap": dil.trap,
                "dil_growth": dil.growth,
                "days_since_report": days_since_report(ctx.report_dates, as_of),
                "record_ids": "|".join(rows["record_id"]),
            }
        )
    return pd.DataFrame(rows_out)


def build_b_events(register: Register, cfg: dict, market: MarketLookup = _no_market) -> pd.DataFrame:
    dc, rc, lc, sy = cfg["dilution"], cfg["routine"], cfg["large_holder"], cfg["symbolic"]
    min_persons = cfg["cluster"]["min_persons"]
    rows_out = []
    for issuer in register.issuers:
        for trig in detect_clusters(register, issuer, cfg):
            v = register.visible(trig.as_of, issuer)
            window = v[v["record_id"].isin(trig.record_ids)]
            isin = _mode(window["isin"])
            ctx = market(issuer, isin)
            last_buy = window["trade_date"].max()
            dil = dilution_verdict(v, last_buy, trig.as_of, dc, ctx.shares, ctx.splits)
            shares_out = ctx.shares_asof(trig.as_of, dc["shares_lag_days"])
            persons = []
            for person in trig.persons:
                m = routine_metrics(v, person, trig.as_of, rc)
                own = window[window["person_key"].eq(person)]
                before = v[v["trade_date"] < own["trade_date"].min()]
                persons.append(
                    {
                        "person": person,
                        "routine": m.is_routine,
                        "cmp": m.cmp_label,
                        "large_holder": large_holder(v, person, shares_out, lc["position_share_threshold"]),
                        "symbolic": symbolic_purchase(before, person, float(own["volume"].sum()), sy["max_position_change"]),
                    }
                )
            non_routine = sum(1 for p in persons if not p["routine"])
            any_large = any(p["large_holder"] == "true" for p in persons)
            layer = Layer1(
                cluster=True,
                not_routine=non_routine >= min_persons,
                dilution_ok=dil.verdict != "BLOCKED",
                no_large_holder=not any_large,
                structural_s3=trig.s3_in_window,
            )
            flags = context_flags(v, trig.anchor - pd.Timedelta(days=30), trig.as_of)
            rows_out.append(
                {
                    "issuer_key": issuer,
                    "as_of": trig.as_of,
                    "event_day": trig.as_of.normalize(),
                    "anchor": trig.anchor,
                    "window_end": trig.window_end,
                    "isin": isin,
                    "issuer_name": _mode(window["issuer_name_raw"]) if "issuer_name_raw" in window else None,
                    "n_persons": len(trig.persons),
                    "persons": "|".join(trig.persons),
                    "n_rows": len(window),
                    "value_sek": float(window["value_sek"].sum()),
                    "value_usd": float(window["value_usd"].sum()),
                    "staleness_days": trig.staleness_days,
                    "is_stale": trig.is_stale,
                    "s3_in_window": trig.s3_in_window,
                    "uniform_onvenue": trig.uniform_onvenue_in_window,
                    **flags,
                    "n_routine": sum(1 for p in persons if p["routine"]),
                    "n_large_holder": sum(1 for p in persons if p["large_holder"] == "true"),
                    "n_symbolic": sum(1 for p in persons if p["symbolic"] == "true"),
                    "cmp_labels": "|".join(p["cmp"] for p in persons),
                    "dilution": dil.verdict,
                    "dil_participation": dil.participation,
                    "dil_trap": dil.trap,
                    "dil_growth": dil.growth,
                    "not_routine": layer.not_routine,
                    "dilution_ok": layer.dilution_ok,
                    "no_large_holder": layer.no_large_holder,
                    "score": layer.score,
                    "days_since_report": days_since_report(ctx.report_dates, trig.as_of),
                    "record_ids": "|".join(trig.record_ids),
                }
            )
    return pd.DataFrame(rows_out)


def apply_cooldown(events: pd.DataFrame, days: int, date_col: str = "event_day") -> pd.DataFrame:
    """Variante (b): per emittente, evento successivo solo oltre `days` giorni di calendario dall'ultimo tenuto."""
    if events.empty:
        return events
    keep = []
    gap = pd.Timedelta(days=days)
    for _, grp in events.sort_values([date_col]).groupby("issuer_key", sort=False):
        last = None
        for idx, day in zip(grp.index, grp[date_col]):
            if last is None or day - last > gap:
                keep.append(idx)
                last = day
    return events.loc[sorted(keep)]
