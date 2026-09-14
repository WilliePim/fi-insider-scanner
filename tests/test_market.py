import numpy as np
import pandas as pd
import pytest

from fi_insider_scanner.market.fx import FxOrientationError, attach_values, check_orientation
from fi_insider_scanner.market.prices import raw_close, split_factor_after, verify_against_register

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
