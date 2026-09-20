import pandas as pd

from fi_insider_scanner.canon.mapping import assign_issuer_keys, map_row, map_rows
from fi_insider_scanner.ingest.rawcsv import EXPECTED_HEADER


def raw(line: str, record_id: str = "r:0") -> dict:
    fields = line.split(";")
    assert len(fields) == len(EXPECTED_HEADER)
    return {"record_id": record_id, **dict(zip(EXPECTED_HEADER, fields, strict=True))}


VIMIAN = (
    "2026-09-13 22:54:41;Vimian Group AB;549300OQ8R5TCAP0BS18;Eva-Lotta Lundaas;Eva-Lotta Lundaas;"
    "Annan medlem i bolagets administrations-, lednings- eller kontrollorgan;;Ja;Befattning (fel i tidigare rapportering);;;"
    "Förvärv;Aktie;Vimian E1 2026;SE0029856129;2026-08-28 00:00:00;27624,0;Antal;6,88;SEK;Utanför handelsplats;Aktuell"
)
ARLON = (
    "2021-05-10 08:00:00;Testbolaget AB;549300OQ8R5TCAP0BS18;Arlon Capital AB;Magnus Lindquist;"
    "Styrelseledamot/suppleant;Ja;;;Ja;;Förvärv;Aktie;Testbolaget ser. B;SE0000108656;2021-05-07 00:00:00;"
    "10000,0;Antal;25,40;SEK;NASDAQ STOCKHOLM AB;Aktuell"
)
OLD_2017 = (
    "2017-03-02 10:00:00;Gammal AB;;Per Persson;Per Persson;VD;;;;Ja;;Förvärv;;Gammal AB;SE0008613731;"
    "2017-03-01 00:00:00;5000,0;Antal;12,5;SEK;AKTIETORGET;Aktuell"
)
CAD_ROW = (
    "2022-11-01 09:00:00;Lundin Test Corp;;Anna Lund;Anna Lund;Director;;;;Ja;;Förvärv;Aktie;Lundin Test;"
    "CA5503721063;2022-10-28 00:00:00;2000,0;Antal;7,15;CAD;TORONTO STOCK EXCHANGE;Aktuell"
)
BELOPP = (
    "2020-04-02 09:00:00;Testbolaget AB (publ);;Anna Svensson;Anna Svensson;Verkställande direktör (VD);;;;Ja;;"
    "Förvärv;Konvertibel;Testbolaget KV 2023;SE0000108656;2020-04-01 00:00:00;500000,0;Belopp;100,0;SEK;Utanför handelsplats;Aktuell"
)


def test_vimian_correction_row():
    t = map_row(raw(VIMIAN), "bulk", "snap")
    assert t.is_amendment is True and t.is_initial is False
    assert t.txn_kind == "acq_purchase" and t.direction == 1
    assert t.volume == 27624.0 and t.price == 6.88 and t.currency == "SEK"
    assert t.venue_class == "off_venue"
    assert t.roles == ("other_admin_body",)
    assert t.lei_checksum_ok and t.isin_valid
    assert t.share_class is None
    assert t.parse_errors == ()


def test_closely_associated_vehicle_is_attributed_to_pdmr():
    t = map_row(raw(ARLON), "bulk", "snap")
    assert t.is_closely_associated is True
    assert t.associate_kind == "vehicle"
    assert t.name_key == "magnus lindquist"
    assert t.pdmr_is_natural_person is True
    assert set(t.roles) == {"board", "deputy_board"}
    assert t.share_class == "B"
    assert t.venue_class == "xsto"


def test_old_row_without_instrument_type_keeps_null_reported_type():
    t = map_row(raw(OLD_2017), "bulk", "snap")
    assert t.instrument_type_raw is None and t.instrument_type_reported is None
    assert t.venue_class == "spotlight"


def test_native_currency_is_kept():
    t = map_row(raw(CAD_ROW), "bulk", "snap")
    assert t.currency == "CAD" and t.price == 7.15
    assert t.venue_class == "foreign_exchange"


def test_amount_unit_row():
    t = map_row(raw(BELOPP), "bulk", "snap")
    assert t.volume_unit == "belopp"
    assert t.instrument_type_reported == "convertible"


def test_invariant_violation_is_recorded_not_fatal():
    line = VIMIAN.replace(";Ja;Befattning (fel i tidigare rapportering);;;", ";Ja;x;Ja;;")
    t = map_row(raw(line), "bulk", "snap")
    assert "KORRIGERING_INVARIANT_VIOLATION" in t.parse_errors


def test_unparseable_publication_date_is_rejected():
    df, rejects = map_rows(pd.DataFrame([raw(VIMIAN, "a:0"), raw(";" + VIMIAN.split(";", 1)[1], "b:0")]), "bulk", "snap")
    assert len(df) == 1 and list(rejects["record_id"]) == ["b:0"]


def test_issuer_key_backfill_from_isin():
    rows = [raw(ARLON, "a:0"), raw(ARLON.replace("549300OQ8R5TCAP0BS18", "").replace("2021-05-10", "2021-06-10"), "b:0")]
    df, _ = map_rows(pd.DataFrame(rows), "bulk", "snap")
    df = assign_issuer_keys(df)
    assert list(df["issuer_key"]) == ["549300OQ8R5TCAP0BS18", "549300OQ8R5TCAP0BS18"]
    assert list(df["issuer_key_source"]) == ["lei", "isin_backfill"]


def test_issuer_key_falls_back_to_name():
    df, _ = map_rows(pd.DataFrame([raw(OLD_2017)]), "bulk", "snap")
    df = assign_issuer_keys(df)
    assert df.loc[0, "issuer_key"] == "name:gammal"
    assert df.loc[0, "issuer_key_source"] == "name"
