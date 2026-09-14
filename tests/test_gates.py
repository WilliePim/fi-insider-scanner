import pandas as pd
from factory import T, register, txn, visible_all

from fi_insider_scanner.gates.closed_period import days_since_report, window_label
from fi_insider_scanner.gates.dilution import dilution_verdict, share_growth
from fi_insider_scanner.gates.large_holder import large_holder, position_lb, symbolic_purchase
from fi_insider_scanner.gates.routine import routine_metrics
from fi_insider_scanner.gates.score import Layer1

DC = {
    "participation_days": 5, "trap_days": 75, "growth_blocked": 0.25, "growth_caution": 0.10,
    "baseline_gap_min_days": 180, "baseline_gap_max_days": 700, "shares_lag_days": 45,
}
RC = {"lookback_days": 365, "min_months": 6, "max_dispersion": 0.25}


def shares(*obs):
    return pd.Series([s for _, s in obs], index=pd.DatetimeIndex([T(d) for d, _ in obs]))


def test_growth_blocked_and_not_yet_public():
    s = shares(("2019-01-15", 10_000_000), ("2020-01-10", 13_000_000))
    v = visible_all([txn()])
    assert dilution_verdict(v, T("2020-03-01"), T("2020-03-15"), DC, s).verdict == "BLOCKED"
    # a 2020-02-01 l'osservazione del 2020-01-10 non è ancora pubblica (lag 45): resta solo il 2019 -> nessuna baseline
    assert dilution_verdict(v, T("2020-01-25"), T("2020-02-01"), DC, s).verdict == "UNKNOWN"


def test_split_normalized_growth_is_zero():
    s = shares(("2019-01-15", 10_000_000), ("2020-01-10", 20_000_000))
    splits = pd.Series([2.0], index=pd.DatetimeIndex([T("2019-06-01")]))
    assert share_growth(s, splits, T("2020-03-15"), DC) == 0.0
    assert dilution_verdict(visible_all([txn()]), T("2020-03-01"), T("2020-03-15"), DC, s, splits).verdict == "CLEAR"


def test_caution_and_short_gap():
    s = shares(("2019-01-15", 10_000_000), ("2020-01-10", 11_500_000))
    assert dilution_verdict(visible_all([txn()]), T("2020-03-01"), T("2020-03-15"), DC, s).verdict == "CAUTION"
    short = shares(("2019-08-13", 10_000_000), ("2020-01-10", 13_000_000))
    assert share_growth(short, None, T("2020-03-15"), DC) is None


def test_participation_and_trap_respect_visibility():
    buy = txn("anna svensson", "2020-03-10")
    part = txn("erik berg", "2020-03-07", "2020-03-08 09:00", kind="subscription")
    trap = txn("erik berg", "2020-03-30", "2020-04-02 09:00", kind="subscription")
    reg = register([buy, part, trap])
    early = reg.visible(T("2020-03-11 12:00"), "LEI1")
    assert dilution_verdict(early, T("2020-03-10"), T("2020-03-11 12:00"), DC).participation
    reg2 = register([buy, trap])
    before = reg2.visible(T("2020-03-11 12:00"), "LEI1")
    assert dilution_verdict(before, T("2020-03-10"), T("2020-03-11 12:00"), DC).verdict == "UNKNOWN"
    after = reg2.visible(T("2020-04-03"), "LEI1")
    assert dilution_verdict(after, T("2020-03-10"), T("2020-04-03"), DC).trap


def test_large_holder_true_or_unknown_never_false():
    v = visible_all([txn("anna svensson", roles=("owner_keyword",))])
    assert large_holder(v, "anna svensson", None, 0.10) == "true"
    big = visible_all([txn("erik berg", volume=1_200_000)])
    assert position_lb(big, "erik berg") == 1_200_000
    assert large_holder(big, "erik berg", 10_000_000, 0.10) == "true"
    small = visible_all([txn("erik berg", volume=500_000)])
    assert large_holder(small, "erik berg", 10_000_000, 0.10) == "unknown"
    assert large_holder(small, "erik berg", None, 0.10) == "unknown"


def test_symbolic_purchase_upper_bound():
    before = visible_all([txn("erik berg", volume=2_000_000)])
    assert symbolic_purchase(before, "erik berg", 10_000, 0.01) == "true"
    assert symbolic_purchase(before, "erik berg", 100_000, 0.01) == "unknown"
    assert symbolic_purchase(visible_all([txn("anna svensson")]), "erik berg", 10, 0.01) == "unknown"


def test_routine_monthly_equal_buys():
    rows = [txn("anna svensson", f"2019-{m:02d}-15", price=10.0, volume=1000.0) for m in range(3, 13)]
    v = visible_all(rows)
    m = routine_metrics(v, "anna svensson", T("2020-01-20"), RC)
    assert m.n_buy_months == 10 and m.dispersion == 0.0 and m.is_routine


def test_routine_sporadic_and_future_rows_excluded():
    rows = [txn("anna svensson", d, volume=vol) for d, vol in (("2019-04-10", 1000), ("2019-07-10", 50000), ("2019-10-10", 3000))]
    rows.append(txn("anna svensson", "2020-02-10", "2020-02-11 09:00"))
    reg = register(rows)
    m = routine_metrics(reg.visible(T("2020-01-01"), "LEI1"), "anna svensson", T("2020-01-01"), RC)
    assert m.n_buy_months == 3 and not m.is_routine


def test_cmp_label_is_per_person():
    rows = [txn("anna svensson", f"{y}-05-10") for y in (2017, 2018, 2019)]
    rows += [txn("erik berg", "2019-05-10")]
    v = visible_all(rows)
    assert routine_metrics(v, "anna svensson", T("2020-03-01"), RC).cmp_label == "routine"
    assert routine_metrics(v, "erik berg", T("2020-03-01"), RC).cmp_label == "sparse"


def test_closed_period():
    reports = pd.DatetimeIndex([T("2020-02-10"), T("2020-04-24"), T("2020-07-15")])
    assert days_since_report(reports, T("2020-04-28")) == 4
    assert window_label(4, 10) == "IN_POST_REPORT_WINDOW"
    assert window_label(40, 10) == "OUTSIDE"
    assert days_since_report(None, T("2020-04-28")) is None
    assert window_label(None, 10) == "UNKNOWN"


def test_layer1_score():
    assert Layer1(True, True, True, True, False).score == 4
    assert Layer1(True, False, True, True, False).score == 3
    assert Layer1(True, True, True, True, True).score == 0
