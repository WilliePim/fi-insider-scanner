import numpy as np
import pandas as pd
import pytest

from fi_insider_scanner.market.fx import FxOrientationError, attach_values, check_orientation
from fi_insider_scanner.market.prices import (
    estimate_scale_segments,
    raw_close,
    scale_at,
    split_factor_after,
    verify_against_register,
)

T = pd.Timestamp


def fx_series():
    days = pd.date_range("2020-01-01", "2020-03-31", freq="B")
    return {"USD": pd.Series(10.0, index=days), "EUR": pd.Series(11.0, index=days)}


def test_attach_values_native_to_sek_and_usd():
    df = pd.DataFrame(
        {
            "volume": [10000.0, 1000.0, 500.0, 100.0],
            "price": [25.4, 5.0, 2.0, 1.0],
            "volume_unit": ["antal", "antal", "antal", "belopp"],
            "currency": ["SEK", "EUR", "BWP", "SEK"],
            "trade_date": [T("2020-03-13"), T("2020-03-14"), T("2020-03-13"), T("2020-03-13")],
        }
    )
    out = attach_values(df, fx_series())
    assert out.loc[0, "value_sek"] == pytest.approx(254000.0)
    assert out.loc[0, "value_usd"] == pytest.approx(25400.0)
    # sabato 14/3: tasso del venerdì 13/3, data salvata
    assert out.loc[1, "fx_sek_per_unit"] == 11.0 and out.loc[1, "fx_date"] == T("2020-03-13")
    assert out.loc[1, "value_sek"] == pytest.approx(55000.0)
    assert np.isnan(out.loc[2, "value_sek"])  # valuta senza serie: null, non stimato
    assert np.isnan(out.loc[3, "value_native"])  # Belopp: nessun valore per azioni


def test_fx_orientation_guard():
    with pytest.raises(FxOrientationError):
        check_orientation({"USD": pd.Series([0.1, 0.1])})


def _history(closes, splits=None, start="2019-01-01"):
    idx = pd.date_range(start, periods=len(closes), freq="B")
    h = pd.DataFrame({"Close": closes, "Low": np.array(closes) * 0.98, "High": np.array(closes) * 1.02}, index=idx)
    h["Stock Splits"] = 0.0
    for day, ratio in (splits or {}).items():
        h.loc[T(day), "Stock Splits"] = ratio
    return h


def test_raw_close_reconstructs_pre_split_price():
    h = _history([10.0] * 400, splits={"2020-06-01": 2.0})
    assert raw_close(h, pd.Series([T("2019-01-02")]))[0] == pytest.approx(20.0)
    assert raw_close(h, pd.Series([T("2020-06-02")]))[0] == pytest.approx(10.0)
    assert split_factor_after(h, pd.Series([T("2020-06-01")]))[0] == 1.0  # lo split del giorno è già nel prezzo


def test_verify_against_register():
    h = _history(list(np.linspace(10, 12, 60)))
    days = h.index[[5, 15, 25, 35, 45]]
    ok = pd.DataFrame({"trade_date": days, "price": h.loc[days, "Close"].to_numpy()})
    assert verify_against_register(h, ok, 0.02, 3, 0.8).verified is True
    scaled = ok.assign(price=ok["price"] * 100)
    v = verify_against_register(h, scaled, 0.02, 3, 0.8)
    assert v.verified is False and v.reason == "SCALE_SUSPECT"
    assert verify_against_register(h, ok.head(2), 0.02, 3, 0.8).verified is None
    assert verify_against_register(None, ok, 0.02, 3, 0.8).reason == "NO_HISTORY"


def test_yahoo_rescaled_history_is_detected_and_verification_uses_recent_rows():
    # Yahoo rescaled the history before 2020-06-01 by 1/1.2 (a rights issue); the register holds the real prices
    idx = pd.date_range("2019-01-01", "2021-12-31", freq="B")
    true_close = np.full(len(idx), 100.0)
    yahoo_close = np.where(idx < pd.Timestamp("2020-06-01"), true_close / 1.2, true_close)
    h = pd.DataFrame({"Close": yahoo_close, "Low": yahoo_close * 0.99, "High": yahoo_close * 1.01}, index=idx)
    h["Stock Splits"] = 0.0
    days = idx[::25]
    trades = pd.DataFrame({"trade_date": days, "price": np.full(len(days), 100.0)})
    v = verify_against_register(h, trades, 0.02, 3, 0.8)
    assert v.verified is True and v.adjusted_history is True
    assert v.share_in_range < 0.8 <= v.share_in_range_recent
    segs = estimate_scale_segments(h, trades)
    assert len(segs) == 2
    assert segs[0].factor == pytest.approx(1.2, rel=0.01) and segs[1].factor == pytest.approx(1.0, rel=0.01)
    early = raw_close(h, pd.Series([T("2019-03-01")]), segs)[0]
    assert early == pytest.approx(100.0, rel=0.01)
    assert scale_at(segs, pd.Series([T("2018-01-01")]))[0] == pytest.approx(1.2, rel=0.01)  # prima di ogni tratto: il più vicino


def test_recent_mismatch_is_still_rejected():
    idx = pd.date_range("2019-01-01", "2021-12-31", freq="B")
    close = np.full(len(idx), 100.0)
    h = pd.DataFrame({"Close": close, "Low": close * 0.99, "High": close * 1.01}, index=idx)
    h["Stock Splits"] = 0.0
    days = idx[::25]
    trades = pd.DataFrame({"trade_date": days, "price": np.full(len(days), 150.0)})
    assert verify_against_register(h, trades, 0.02, 3, 0.8).verified is False
