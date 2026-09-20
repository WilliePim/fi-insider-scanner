from factory import T, register, txn, visible_all
from fi_insider_scanner.gates.clusters import detect_clusters
from fi_insider_scanner.gates.structural import context_flags, uniform_price_groups

CFG = {
    "cluster": {"min_persons": 3, "window_days": 30, "max_staleness_days": 30, "episode_cooldown_days": 30},
    "structural": {"min_persons_same_price": 3, "subscription_price_window_days": 20},
}


def trio(venue="off_venue", price=3.5, pub_third="2020-03-04 10:00"):
    return [
        txn("p1 one", "2020-03-02", "2020-03-03 10:00", price=price, venue=venue),
        txn("p2 two", "2020-03-02", "2020-03-03 10:00", price=price, venue=venue),
        txn("p3 three", "2020-03-02", pub_third, price=price, venue=venue),
    ]


def test_s3_off_venue_three_persons_same_price():
    groups = uniform_price_groups(visible_all(trio()), 3, 20)
    assert len(groups) == 1 and bool(groups.loc[0, "s3"]) and bool(groups.loc[0, "off_venue"])


def test_uniform_price_on_venue_without_issue_is_only_a_flag():
    groups = uniform_price_groups(visible_all(trio(venue="xsto")), 3, 20)
    assert not bool(groups.loc[0, "s3"]) and bool(groups.loc[0, "uniform_onvenue"])


def test_on_venue_uniform_price_with_subscription_at_same_price_is_s3():
    rows = [*trio(venue="xsto"), txn("p4 four", "2020-03-15", kind="subscription", price=3.5, venue="off_venue")]
    groups = uniform_price_groups(visible_all(rows), 3, 20)
    assert bool(groups.loc[0, "s3"]) and bool(groups.loc[0, "issue_evidence"])


def test_two_persons_is_not_a_group():
    groups = uniform_price_groups(visible_all(trio()[:2]), 3, 20)
    assert groups.empty


def test_s3_is_point_in_time():
    reg = register(trio(pub_third="2020-03-10 10:00"))
    assert uniform_price_groups(reg.visible(T("2020-03-05"), "LEI1"), 3, 20).empty
    assert not uniform_price_groups(reg.visible(T("2020-03-11"), "LEI1"), 3, 20).empty


def test_s3_rows_do_not_count_toward_cluster():
    rows = [
        txn("p4 four", "2020-02-25", "2020-02-26 09:00", kind="subscription", price=3.5, venue="off_venue"),
        txn("p1 one", "2020-03-02", price=3.5, venue="xsto"),
        txn("p2 two", "2020-03-02", price=3.5, venue="xsto"),
        txn("p3 three", "2020-03-02", price=3.5, venue="xsto"),
    ]
    assert detect_clusters(register(rows), "LEI1", CFG) == []


def test_issue_evidence_published_after_trigger_does_not_rewrite_the_past():
    rows = [
        txn("p1 one", "2020-03-02", price=3.5, venue="xsto"),
        txn("p2 two", "2020-03-02", price=3.5, venue="xsto"),
        txn("p3 three", "2020-03-02", price=3.5, venue="xsto"),
        txn("p4 four", "2020-03-10", "2020-03-11 09:00", kind="subscription", price=3.5, venue="off_venue"),
    ]
    trig = detect_clusters(register(rows), "LEI1", CFG)
    assert len(trig) == 1 and trig[0].as_of == T("2020-03-03 09:00")
    assert trig[0].uniform_onvenue_in_window and not trig[0].s3_in_window


def test_context_flags():
    rows = [txn("p1 one", "2020-03-02", kind="subscription"), txn("p2 two", "2020-03-03", itype="bta")]
    flags = context_flags(visible_all(rows), T("2020-03-01"), T("2020-03-31"))
    assert flags == {"s1_subscription": True, "s2_issue_instruments": True}
