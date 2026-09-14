from factory import T, register, txn

from fi_insider_scanner.gates.clusters import detect_clusters

CFG = {
    "cluster": {"min_persons": 3, "window_days": 30, "max_staleness_days": 30, "episode_cooldown_days": 30},
    "structural": {"min_persons_same_price": 3, "subscription_price_window_days": 20},
}
D = T("2020-03-02")


def day(n: int, hour: int = 0) -> str:
    return str(D + __import__("pandas").Timedelta(days=n, hours=hour))


def base_trio(third_trade: int = 29, third_pub: int = 31):
    return [
        txn("p1 one", day(0), day(2, 10), price=10.0),
        txn("p2 two", day(10), day(12, 10), price=10.5),
        txn("p3 three", day(third_trade), day(third_pub, 10), price=11.0),
    ]


def test_trigger_at_publication_of_third_person():
    trig = detect_clusters(register(base_trio()), "LEI1", CFG)
    assert len(trig) == 1
    t = trig[0]
    assert t.as_of == T(day(31, 10))
    assert t.anchor == D and t.staleness_days == 2 and not t.is_stale
    assert len(t.persons) == 3


def test_window_is_inclusive_30_days():
    assert len(detect_clusters(register(base_trio(third_trade=30, third_pub=32)), "LEI1", CFG)) == 1
    assert detect_clusters(register(base_trio(third_trade=31, third_pub=33)), "LEI1", CFG) == []


def test_stale_trigger():
    trig = detect_clusters(register(base_trio(third_trade=5, third_pub=90)), "LEI1", CFG)
    assert len(trig) == 1 and trig[0].staleness_days == 85 and trig[0].is_stale


def test_vehicle_and_person_count_once():
    rows = [
        txn("p1 one", day(0), day(1, 10)),
        txn("p1 one", day(3), day(4, 10)),  # stessa PDMR via veicolo: name_key identico
        txn("p2 two", day(5), day(6, 10)),
    ]
    assert detect_clusters(register(rows), "LEI1", CFG) == []


def test_entity_pdmr_does_not_count():
    rows = base_trio()
    rows[2] = txn("holding ab", day(29), day(31, 10), natural=False)
    assert detect_clusters(register(rows), "LEI1", CFG) == []


def test_episode_cooldown():
    first = base_trio()  # fine episodio = giorno 29
    second_close = [txn(f"q{i} x", day(29 + 30 + i * 0), day(60 + i, 10)) for i in range(3)]
    assert len(detect_clusters(register(first + second_close), "LEI1", CFG)) == 1
    second_far = [txn(f"q{i} x", day(29 + 31), day(62 + i, 10)) for i in range(3)]
    assert len(detect_clusters(register(first + second_far), "LEI1", CFG)) == 2


def test_snapshot_vs_as_seen_with_cancelled_row():
    rows = base_trio()
    rows[2]["chain_status"] = "cancelled"
    assert detect_clusters(register(rows, mode="snapshot"), "LEI1", CFG) == []
    assert len(detect_clusters(register(rows, mode="as_seen"), "LEI1", CFG)) == 1


def test_first_pub_timing_moves_trigger_earlier():
    rows = base_trio()
    rows[2]["first_published_at"] = T(day(30, 9))
    trig = detect_clusters(register(rows, timing="first_pub"), "LEI1", CFG)
    assert trig[0].as_of == T(day(30, 9))
