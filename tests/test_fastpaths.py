"""The optimised hot paths must behave exactly like the obvious slow implementations."""

import numpy as np
import pandas as pd
import pytest

from factory import T, frame, register, txn
from fi_insider_scanner.backtest.run import Env
from fi_insider_scanner.gates.clusters import find_window

CFG = {"dilution": {"shares_lag_days": 45}, "band": {"low_usd": 50e6, "high_usd": 300e6, "edge_sensitivity": 0.2}}


def slow_find_window(rows: pd.DataFrame, min_persons: int, window_days: int, min_anchor=None):
    """Reference implementation: quadratic scan over anchors."""
    r = rows if min_anchor is None else rows[rows["trade_date"] >= min_anchor]
    r = r.sort_values(["trade_date", "record_id"], kind="stable")
    dates, persons = r["trade_date"].to_numpy(), r["person_key"].to_numpy()
    span = np.timedelta64(window_days, "D")
    for i in range(len(r)):
        j = int(dates.searchsorted(dates[i] + span, side="right"))
        if len(set(persons[i:j])) >= min_persons:
            return r.iloc[i:j]
    return None


def random_rows(seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = [
        txn(f"p{rng.integers(0, 5)} x", str((T("2020-01-01") + pd.Timedelta(days=int(rng.integers(0, 120)))).date()))
        for _ in range(int(rng.integers(3, 25)))
    ]
    return frame(rows).assign(person_key=lambda d: d["name_key"])


@pytest.mark.parametrize("seed", range(40))
def test_sliding_window_matches_quadratic_scan(seed):
    rows = random_rows(seed)
    for min_anchor in (None, T("2020-02-01")):
        fast = find_window(rows, 3, 30, min_anchor)
        slow = slow_find_window(rows, 3, 30, min_anchor)
        assert (fast is None) == (slow is None), seed
        if fast is not None:
            assert list(fast["record_id"]) == list(slow["record_id"]), seed


def test_window_boundaries():
    rows = frame([txn("a one", "2020-03-02"), txn("b two", "2020-03-20"), txn("c three", "2020-04-01")]).assign(
        person_key=lambda d: d["name_key"]
    )
    assert find_window(rows, 3, 30, None) is not None  # 2 marzo + 30 giorni include il 1 aprile
    assert find_window(rows, 3, 29, None) is None
    assert find_window(rows, 3, 30, T("2020-03-03")) is None  # l'ancora esclude la prima riga


def env_with(rows: list[dict]) -> Env:
    current = frame(rows)
    current["type_source"] = "reported"
    current["instrument_type"] = "share"
    current["share_class"] = None
    return Env(CFG, market=None, bench=None, usdsek=None, current=current)


def test_register_price_prefers_on_venue_median():
    rows = [
        txn("a one", price=10.0, venue="xsto", isin="SE0000108656"),
        txn("b two", price=12.0, venue="xsto", isin="SE0000108656"),
        txn("c three", price=99.0, venue="off_venue", isin="SE0000108656"),
    ]
    env = env_with(rows)
    ids = "|".join(env.current["record_id"])
    assert env.register_price(ids, "SE0000108656") == (11.0, "register_onvenue")


def test_register_price_falls_back_off_venue_and_filters():
    rows = [
        txn("a one", price=8.0, venue="off_venue", isin="SE0000108656"),
        txn("b two", price=500.0, venue="xsto", isin="SE0000108656", currency="EUR"),
        txn("c three", price=0.0, venue="xsto", isin="SE0000108656"),
        txn("d four", price=44.0, venue="xsto", isin="SE0008613731"),
    ]
    env = env_with(rows)
    ids = "|".join(env.current["record_id"])
    assert env.register_price(ids, "SE0000108656") == (8.0, "register_offvenue")
    assert env.register_price(ids, "SE0008613731") == (44.0, "register_onvenue")
    assert env.register_price("missing:0", "SE0000108656") == (None, None)


def test_weak_type_flags_inferred_rows():
    env = env_with([txn("a one"), txn("b two")])
    ids = list(env.current["record_id"])
    env.type_source[ids[1]] = "isin_majority"
    assert env.weak_type(ids[0]) is False
    assert env.weak_type("|".join(ids)) is True


def test_visible_since_filters_trade_dates_only():
    rows = [txn("a one", "2020-01-10", "2020-01-11 09:00"), txn("b two", "2020-06-10", "2020-06-11 09:00")]
    reg = register(rows)
    full = reg.visible(T("2020-07-01"), "LEI1")
    recent = reg.visible(T("2020-07-01"), "LEI1", since=T("2020-03-01"))
    assert len(full) == 2 and len(recent) == 1
    assert recent.iloc[0]["trade_date"] == T("2020-06-10")
    assert "person_key" in recent


def test_visible_person_key_without_merge_rules_is_the_name_key():
    reg = register([txn("anna svensson", "2020-01-10")])
    visible = reg.visible(T("2020-02-01"), "LEI1")
    assert list(visible["person_key"]) == ["anna svensson"]
