import numpy as np
import pandas as pd
import pytest

from fi_insider_scanner.backtest.stats import Summary
from fi_insider_scanner.backtest.survivorship import acquired_likely, break_even_share, scenario_values
from fi_insider_scanner.backtest.verdict import decide

T = pd.Timestamp


def test_scenario_values():
    obs = np.array([0.1, -0.2, 0.3])
    assert scenario_values("S_minus100", 2, 0.10, 0.15, obs, 1) == pytest.approx([-1.10, -1.10])
    assert scenario_values("S_minus50", 1, 0.10, 0.15, obs, 1) == pytest.approx([-0.60])
    assert scenario_values("S0", 1, 0.10, 0.15, obs, 1) == pytest.approx([0.0])
    assert scenario_values("S_plus", 1, 0.10, 0.15, obs, 1) == pytest.approx([0.15])
    a = scenario_values("S_draw", 50, 0.10, 0.15, obs, 7)
    assert np.array_equal(a, scenario_values("S_draw", 50, 0.10, 0.15, obs, 7))
    assert set(np.round(a, 6)) <= set(np.round(obs, 6))


def test_break_even_share():
    # 100 osservati a media +3%, 20 non risolti, benchmark +5%: p* = 3 / (20 * 1,05)
    p = break_even_share(0.03, 100, 20, 0.05)
    assert p == pytest.approx(3 / 21)
    added = int(round(p * 20 * 1000)) / 1000  # verifica: la media si annulla
    mean = (100 * 0.03 + p * 20 * (-1 - 0.05)) / (100 + p * 20)
    assert mean == pytest.approx(0.0, abs=1e-12)
    assert break_even_share(-0.01, 100, 20, 0.05) is None


def test_acquired_likely():
    rows = pd.DataFrame(
        {
            "issuer_key": ["X", "X", "X", "Y", "Y"],
            "trade_date": [T("2019-01-10"), T("2019-01-12"), T("2019-02-01"), T("2019-01-10"), T("2019-02-01")],
            "txn_kind": ["disp_sale", "disp_sale", "acq_purchase", "disp_sale", "acq_purchase"],
            "venue_class": ["off_venue", "off_venue", "xsto", "xsto", "xsto"],
            "price": [50.0, 50.0, 30.0, 50.0, 30.0],
            "name_key": ["a b", "c d", "e f", "a b", "e f"],
        }
    )
    assert acquired_likely(rows, 120) == {"X"}


def summary(mean, t, ci=(0.01, 0.05), mde_=0.02):
    return Summary(n=500, mean=mean, median=mean, sd=0.3, share_positive=0.5, t_iid=t, t_cr1_issuer=t, t_cr1_month=t,
                   t_two_way=t, ci_low=ci[0], ci_high=ci[1], mde=mde_, n_issuers=200, n_months=100)


def test_verdict_rules():
    assert decide(summary(0.03, 2.5), summary(0.02, 2.1), 0.02, 0.8, 0.6).label == "REGGE"
    assert decide(summary(0.03, 2.5), summary(-0.01, -0.5), 0.02, 0.8, 0.6).label == "NON REGGE"
    assert decide(summary(0.005, 0.5, ci=(-0.02, 0.03), mde_=0.03), summary(0.01, 0.8), 0.004, 0.8, 0.6).label == "NON REGGE"
    assert decide(summary(0.005, 0.5, ci=(-0.02, 0.03), mde_=0.06), summary(0.01, 0.8), 0.004, 0.8, 0.6).label == "INCONCLUSIVO"
    low_cov = decide(summary(0.03, 2.5), summary(-0.01, -0.5), 0.02, 0.5, 0.6)
    assert low_cov.label == "INCONCLUSIVO" and "copertura" in low_cov.reasons[0]
    assert decide(summary(0.03, 2.5), None, 0.02, 0.8, 0.6).label == "INCONCLUSIVO"
