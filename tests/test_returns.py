import numpy as np
import pandas as pd
import pytest

from factory import T, register, txn
from fi_insider_scanner.backtest.control import PeerCandidates, QuietIndex, pick_peer
from fi_insider_scanner.backtest.events import apply_cooldown
from fi_insider_scanner.backtest.returns import event_return, monthly_excess
from fi_insider_scanner.market.mcap import band_label, mcap_at, mcap_panel


def bench_series(start="2020-01-01", n=400, growth_from=None, level=100.0, step=1.04):
    idx = pd.bdate_range(start, periods=n)
    vals = np.full(n, level)
    if growth_from is not None:
        vals[growth_from:] = level * step
    return pd.Series(vals, index=idx)


def stock_history(index, closes):
    h = pd.DataFrame({"Close": closes, "Adj Close": closes, "Low": closes, "High": closes}, index=index)
    h["Stock Splits"] = 0.0
    return h


def test_excess_return_and_entry_after_publication():
    # entry at session 0, exit at session 21: the jump has to fall inside the holding window
    bench = bench_series(growth_from=21, step=1.04)
    closes = np.full(len(bench), 10.0)
    closes[21:] = 11.0
    h = stock_history(bench.index, closes)
    event_day = bench.index[0] - pd.Timedelta(days=1)  # entrata alla sessione 0
    r = event_return(h, bench, event_day, 21, 5, 5.0)
    assert r.status == "OK"
    assert r.entry_date == bench.index[0]
    assert r.excess == pytest.approx(0.10 - 0.04, abs=1e-9)
    assert (r.r_stock - 0.01) - r.r_bench == pytest.approx(r.excess - 0.01)


def test_friday_evening_publication_enters_monday_and_holidays_skipped():
    idx = pd.DatetimeIndex([T("2020-03-19"), T("2020-03-20"), T("2020-03-23"), T("2020-04-09"), T("2020-04-14")]).append(
        pd.bdate_range("2020-04-15", periods=200)
    )
    bench = pd.Series(100.0, index=idx)
    h = stock_history(idx, np.full(len(idx), 10.0))
    assert event_return(h, bench, T("2020-03-20 18:00"), 2, 5, 5.0).entry_date == T("2020-03-23")
    assert event_return(h, bench, T("2020-04-09"), 2, 5, 5.0).entry_date == T("2020-04-14")


def test_statuses():
    bench = bench_series(n=300)
    h = stock_history(bench.index[:40], np.full(40, 10.0))
    assert event_return(h, bench, bench.index[0], 126, 5, 5.0).status == "ENDED_IN_WINDOW"
    assert event_return(h, bench, bench.index[250], 126, 5, 5.0).status == "TOO_RECENT"
    assert event_return(None, bench, bench.index[0], 21, 5, 5.0).status == "NO_HISTORY"
    closes = np.full(len(bench), 1.0)
    closes[30:] = 7.0
    assert event_return(stock_history(bench.index, closes), bench, bench.index[0], 126, 5, 5.0).status == "ARTEFACT"


def test_stale_exit_uses_last_bar():
    bench = bench_series(n=300)
    keep = [i for i in range(300) if i not in (126, 127)]
    idx = bench.index[keep]
    h = stock_history(idx, np.full(len(idx), 10.0))
    r = event_return(h, bench, bench.index[0] - pd.Timedelta(days=1), 127, 5, 5.0)
    assert r.status == "OK" and r.stale_exit_sessions == 2


def test_cooldown_variant_b():
    ev = pd.DataFrame({"issuer_key": ["I"] * 3, "event_day": [T("2020-01-01"), T("2020-02-01"), T("2021-06-01")]})
    kept = apply_cooldown(ev, 126)
    assert list(kept["event_day"]) == [T("2020-01-01"), T("2021-06-01")]


def test_monthly_excess_series():
    bench = bench_series(start="2020-01-01", n=70)
    closes = np.linspace(10, 12, 70)
    h = stock_history(bench.index, closes)
    m = monthly_excess(h, bench, bench.index[0], bench.index[-1])
    assert len(m) == 4
    assert np.prod(1 + m["excess"].to_numpy()) == pytest.approx(closes[-1] / closes[0], rel=0.05)


def test_mcap_point_in_time_and_band():
    idx = pd.bdate_range("2018-09-01", "2019-03-01")
    h = stock_history(idx, np.full(len(idx), 10.0))
    h.loc[T("2019-02-01"), "Stock Splits"] = 2.0
    shares = pd.Series([5_000_000.0], index=pd.DatetimeIndex([T("2018-10-15")]))
    p = mcap_at(h, shares, T("2019-01-02"), 45)
    assert p.reason == "OK" and p.close_raw_yahoo == pytest.approx(20.0) and p.mcap_sek == pytest.approx(100_000_000.0)
    assert p.price_source == "yahoo_scaled"
    reg = mcap_at(h, shares, T("2019-01-02"), 45, register_price=21.0, register_price_source="register_onvenue")
    assert (
        reg.mcap_sek == pytest.approx(105_000_000.0)
        and reg.price_source == "register_onvenue"
        and reg.close_raw_yahoo == pytest.approx(20.0)
    )
    after = mcap_at(h, shares, T("2019-02-15"), 45)
    assert after.shares == pytest.approx(10_000_000.0) and after.mcap_sek == pytest.approx(100_000_000.0)
    late = pd.Series([5_000_000.0], index=pd.DatetimeIndex([T("2018-12-20")]))
    assert mcap_at(h, late, T("2019-01-02"), 45).reason == "SHARES_NOT_YET_PUBLIC"
    panel = mcap_panel(h, shares, pd.DatetimeIndex([T("2019-01-02"), T("2019-02-15")]), 45)
    assert panel == pytest.approx([100_000_000.0, 100_000_000.0])
    assert band_label(100_000_000 / 9.0, 50e6, 300e6) == "lt50"
    assert band_label(60e6, 50e6, 300e6) == "50_300"
    assert band_label(300e6, 50e6, 300e6) == "gt300"
    assert band_label(None, 50e6, 300e6) is None


def test_peer_selection():
    pool = pd.DataFrame(
        {
            "issuer_key": ["E", "X", "Y", "Z"],
            "symbol": ["E.ST", "X.ST", "Y.ST", "Z.ST"],
            "mcap_usd": [100e6, 100e6 * np.exp(0.1), 100e6 * np.exp(0.05), 100e6 * np.exp(-0.1)],
            "band": ["50_300"] * 4,
        }
    )
    candidates = PeerCandidates.from_frame(pool)
    peer = pick_peer("E", 100e6, "50_300", candidates, active={"Y"})
    assert peer.issuer_key == "X"  # X e Z a distanza 0,1: vince l'issuer_key minore
    assert peer.symbol == "X.ST"
    assert pick_peer("E", 100e6, "gt300", candidates, active=set()) is None
    assert pick_peer("E", 100e6, "50_300", candidates, active={"X", "Y", "Z"}) is None


def test_quiet_index_is_point_in_time():
    rows = [txn("anna svensson", "2020-03-01", "2020-03-20 09:00", issuer="Y")]
    q = QuietIndex(register(rows))
    assert q.active_issuers(T("2020-03-10"), T("2020-03-10"), 60) == set()
    assert q.active_issuers(T("2020-03-21"), T("2020-03-21"), 60) == {"Y"}
