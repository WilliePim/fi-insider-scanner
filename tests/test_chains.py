import pandas as pd

from fi_insider_scanner.canon.chains import build_chains
from fi_insider_scanner.canon.visibility import Register

T = pd.Timestamp
HORIZON = T("2026-08-16")
COLS = [
    "record_id", "published_at", "issuer_key", "name_key", "trade_date", "status_raw", "is_amendment", "isin",
    "instrument_name", "txn_kind", "volume", "price", "venue_raw", "role_raw", "notifier_name", "currency",
    "amendment_note",
]


def row(rid, pub, status, amendment=False, trade="2020-03-13", isin="SE0000108656", name="Test B", kind="acq_purchase",
        volume=10000.0, price=25.4, person="anna svensson", issuer="LEI1"):
    return {
        "record_id": rid, "published_at": T(pub), "issuer_key": issuer, "name_key": person, "trade_date": T(trade),
        "status_raw": status, "is_amendment": amendment, "isin": isin, "instrument_name": name, "txn_kind": kind,
        "volume": volume, "price": price, "venue_raw": "NASDAQ STOCKHOLM AB", "role_raw": "VD",
        "notifier_name": "Anna Svensson", "currency": "SEK", "amendment_note": "x" if amendment else None,
    }


def chains(rows):
    df, stats = build_chains(pd.DataFrame(rows, columns=COLS), HORIZON)
    return df.set_index("record_id"), stats


def test_correction_links_to_revised_predecessor():
    df, stats = chains([
        row("f03", "2020-03-16 09:00", "Reviderad"),
        row("f04", "2020-03-18 09:00", "Aktuell", amendment=True, volume=1000.0),
    ])
    assert stats.linked == 1
    assert df.loc["f04", "linked_to"] == "f03"
    assert df.loc["f03", "chain_status"] == "superseded"
    assert df.loc["f04", "chain_status"] == "current"
    assert df.loc["f03", "superseded_at"] == T("2020-03-18 09:00")
    assert df.loc["f04", "first_published_at"] == T("2020-03-16 09:00")


def test_snapshot_and_as_seen_visibility():
    df, _ = chains([
        row("f03", "2020-03-16 09:00", "Reviderad"),
        row("f04", "2020-03-18 09:00", "Aktuell", amendment=True, volume=1000.0),
        row("m01", "2020-03-17 09:00", "Makulerad", person="erik berg"),
    ])
    df = df.reset_index()
    snap = Register(df, mode="snapshot")
    seen = Register(df, mode="as_seen")
    assert set(snap.visible(T("2020-03-21"), "LEI1")["record_id"]) == {"f04"}
    assert set(snap.visible(T("2020-03-17 12:00"), "LEI1")["record_id"]) == set()
    assert set(seen.visible(T("2020-03-17 12:00"), "LEI1")["record_id"]) == {"f03", "m01"}
    assert set(seen.visible(T("2020-03-19"), "LEI1")["record_id"]) == {"f04", "m01"}
    first = Register(df, mode="snapshot", timing="first_pub")
    assert set(first.visible(T("2020-03-17"), "LEI1")["record_id"]) == {"f04"}


def test_stale_upstream_status_after_horizon_vimian():
    df, stats = chains([
        row("orig", "2026-09-01 18:24:37", "Aktuell", trade="2026-08-28"),
        row("v2", "2026-09-13 16:18:49", "Reviderad", amendment=True, trade="2026-08-28"),
        row("v3", "2026-09-13 22:54:41", "Aktuell", amendment=True, trade="2026-08-28"),
    ])
    assert df.loc["v3", "linked_to"] == "v2"
    assert df.loc["v2", "linked_to"] == "orig"
    assert df.loc["orig", "chain_status"] == "superseded_inferred"
    assert df.loc["orig", "chain_flags"] == "STATUS_STALE_UPSTREAM"
    assert df.loc["v3", "chain_status"] == "current"
    assert df.loc["v3", "first_published_at"] == T("2026-09-01 18:24:37")
    assert stats.linked_stale == 1


def test_before_horizon_two_current_rows_are_separate_trades():
    df, stats = chains([
        row("a", "2020-03-16 09:00", "Aktuell"),
        row("c", "2020-03-18 09:00", "Aktuell", amendment=True, price=26.0),
    ])
    assert df.loc["a", "chain_status"] == "current" and df.loc["c", "chain_status"] == "current"
    assert pd.isna(df.loc["c", "linked_to"])
    assert stats.orphan_corrections == 1


def test_publication_not_strictly_earlier_is_never_linked():
    df, _ = chains([
        row("r", "2020-03-18 09:00", "Reviderad"),
        row("c", "2020-03-18 09:00", "Aktuell", amendment=True),
    ])
    assert pd.isna(df.loc["c", "linked_to"])
    assert df.loc["r", "chain_status"] == "orphan_revised"


def test_latest_revised_wins_and_earlier_is_orphan():
    df, _ = chains([
        row("r1", "2020-03-10 09:00", "Reviderad"),
        row("r2", "2020-03-12 09:00", "Reviderad"),
        row("c", "2020-03-14 09:00", "Aktuell", amendment=True),
    ])
    assert df.loc["c", "linked_to"] == "r2"
    assert df.loc["r1", "chain_status"] == "orphan_revised"


def test_equal_score_equal_time_is_ambiguous():
    df, stats = chains([
        row("r1", "2020-03-12 09:00", "Reviderad"),
        row("r2", "2020-03-12 09:00", "Reviderad"),
        row("c", "2020-03-14 09:00", "Aktuell", amendment=True),
    ])
    assert stats.ambiguous == 1
    assert pd.isna(df.loc["c", "linked_to"])


def test_nature_change_still_links():
    df, _ = chains([
        row("r", "2020-03-12 09:00", "Reviderad", kind="acq_purchase"),
        row("c", "2020-03-14 09:00", "Aktuell", amendment=True, kind="subscription"),
    ])
    assert df.loc["c", "linked_to"] == "r"


def test_makulerad_is_cancelled():
    df, _ = chains([row("m", "2020-03-12 09:00", "Makulerad")])
    assert df.loc["m", "chain_status"] == "cancelled"
