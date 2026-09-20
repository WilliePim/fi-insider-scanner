import math

import numpy as np
import pandas as pd
import pytest

from fi_insider_scanner.backtest.stats import bootstrap_ci, calendar_time_t, mde, summarize, t_cluster, t_iid, t_two_way


def test_t_iid_known_value():
    assert t_iid([0.1, 0.2, 0.3]) == pytest.approx(3.4641, abs=1e-4)
    assert t_iid([0.1]) is None
    assert t_iid([0.2, 0.2]) is None


def test_singleton_clusters_close_to_iid_scaled():
    x = np.array([0.05, -0.02, 0.10, 0.03, 0.07, -0.01, 0.04, 0.02, 0.06, 0.00, 0.08, 0.01])
    groups = np.arange(len(x))
    # with singleton clusters CR1 = G/(G-1) * sum e^2 / n^2 = the iid variance (ddof=1) / n
    assert t_cluster(x, groups, min_groups=10) == pytest.approx(t_iid(x), rel=1e-9)


def test_cluster_t_requires_enough_groups():
    assert t_cluster([1, 1, -1, -1], ["a", "a", "b", "b"], min_groups=10) is None


def test_cluster_t_hand_computed():
    x = np.array([0.1, 0.3, -0.1, 0.5] * 5)
    g = np.repeat(np.arange(10), 2)
    e = x - x.mean()
    sums = pd.Series(e).groupby(g).sum().to_numpy()
    var = 10 / 9 * np.sum(sums**2) / len(x) ** 2
    assert t_cluster(x, g, 10) == pytest.approx(x.mean() / math.sqrt(var))


def test_two_way_runs_and_bootstrap_is_deterministic():
    rng = np.random.default_rng(0)
    x = rng.normal(0.02, 0.2, 200)
    iss = rng.integers(0, 40, 200)
    mon = rng.integers(0, 30, 200)
    assert t_two_way(x, iss, mon, 10) is not None
    assert bootstrap_ci(x, 500, 7) == bootstrap_ci(x, 500, 7)
    lo, hi = bootstrap_ci([0.05] * 10, 100, 1)
    assert lo == hi == pytest.approx(0.05)


def test_calendar_time_series():
    monthly = pd.DataFrame({"month": ["2020-01", "2020-01", "2020-02", "2020-03"], "excess": [0.02, 0.04, -0.01, 0.05]})
    t, n_months = calendar_time_t(monthly)
    assert n_months == 3
    assert t == pytest.approx(t_iid([0.03, -0.01, 0.05]))


def test_mde_and_summary():
    assert mde(0.46, 600) == pytest.approx((1.959964 + 0.841621) * 0.46 / math.sqrt(600))
    assert mde(0.46, 600) == pytest.approx(0.0526, abs=5e-4)
    s = summarize([0.1, 0.2, 0.3], ["a", "b", "c"], ["m1", "m1", "m2"], draws=100, seed=1)
    assert s.n == 3 and s.mean == pytest.approx(0.2) and s.t_cr1_issuer is None
