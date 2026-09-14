import random

import pytest

from fi_insider_scanner.ingest.rawcsv import EXPECTED_HEADER, SchemaDriftError, parse_register_csv

HEADER = ";".join(EXPECTED_HEADER)
ROW_A = (
    "2020-03-16 09:00:00;Testbolaget AB (publ);549300OQ8R5TCAP0BS18;Anna Svensson;Anna Svensson;"
    "Verkställande direktör (VD);;;;Ja;;Förvärv;Aktie;Testbolaget B;SE0000108656;"
    "2020-03-13 00:00:00;10000,0;Antal;25,40;SEK;NASDAQ STOCKHOLM AB;Aktuell"
)
ROW_B = ROW_A.replace("Anna Svensson;Anna Svensson", "Erik Berg;Erik Berg")
ROW_C = ROW_A.replace("10000,0", "500,0")


def _csv(*lines: str, eol: str = "\r\n") -> bytes:
    return (eol.join((HEADER,) + lines) + eol).encode("utf-8")


def test_header_drift_raises():
    bad = HEADER.replace("Karaktär", "Transaktionstyp")
    with pytest.raises(SchemaDriftError):
        parse_register_csv((bad + "\r\n" + ROW_A + "\r\n").encode("utf-8"))


def test_crlf_and_bom():
    res = parse_register_csv(b"\xef\xbb\xbf" + _csv(ROW_A, ROW_B))
    assert res.had_bom and res.encoding == "utf-8-sig"
    assert len(res.rows) == 2
    assert res.rows.loc[0, "Status"] == "Aktuell"
    assert res.quarantine.empty


def test_fi_export_utf16le_trailing_semicolon_and_nbsp():
    row = ROW_A.replace("Verkställande direktör (VD)", "Annan medlem i bolagets")
    text = "\r\n".join([HEADER + ";", row + ";"]) + "\r\n"
    res = parse_register_csv(text.encode("utf-16-le"))
    assert res.encoding == "utf-16-le"
    assert len(res.rows) == 1
    assert res.rows.loc[0, "Befattning"] == "Annan medlem i bolagets"


def test_record_id_same_for_bulk_and_fi_export_after_cleaning():
    bulk = parse_register_csv(_csv(ROW_A.replace("(VD)", "(VD) ")))
    fi = parse_register_csv(("\r\n".join([HEADER + ";", ROW_A + ";"]) + "\r\n").encode("utf-16-le"))
    assert bulk.rows.loc[0, "record_id"] == fi.rows.loc[0, "record_id"]


def test_identical_tuples_get_distinct_occurrence_ids():
    res = parse_register_csv(_csv(ROW_A, ROW_A))
    ids = list(res.rows["record_id"])
    assert ids[0].endswith(":0") and ids[1].endswith(":1")
    assert ids[0].split(":")[0] == ids[1].split(":")[0]


def test_record_id_stable_when_other_rows_shuffle():
    others = [ROW_B, ROW_C, ROW_A.replace("25,40", "25,50")]
    base = parse_register_csv(_csv(ROW_A, *others))
    rid = base.rows.loc[base.rows["Pris"] == "25,40", "record_id"].iloc[0]
    random.Random(1).shuffle(others)
    shuffled = parse_register_csv(_csv(*others, ROW_A))
    assert rid in set(shuffled.rows["record_id"])


def test_adjacent_unquoted_break_is_joined():
    fields = ROW_A.split(";")
    head, tail = ";".join(fields[:15]), ";".join(fields[15:])
    res = parse_register_csv(_csv(ROW_B, head, tail))
    assert len(res.rows) == 2 and res.quarantine.empty
    joined = res.rows[res.rows["repair"] == "join"].iloc[0]
    assert joined["Transaktionsdatum"] == "2020-03-13 00:00:00"
    assert joined["Status"] == "Aktuell"


def test_non_adjacent_fragments_are_quarantined_not_guessed():
    fields = ROW_A.split(";")
    head, tail = ";".join(fields[:15]), ";".join(fields[15:])
    res = parse_register_csv(_csv(head, ROW_B, ROW_C, tail))
    assert len(res.rows) == 2
    assert sorted(res.quarantine["kind"]) == ["continuation", "truncated"]


def _shifted_pair(row: str) -> tuple[str, str]:
    """Forma reale civictech (Biovica): due record da 22 campi con valori spostati."""
    fields = row.split(";")
    head = ";".join(fields[:15] + [""] * 7)
    tail = ";".join([""] + fields[15:] + [""] * 14)
    return head, tail


def test_shifted_22_field_fragments_non_adjacent_are_quarantined():
    head, tail = _shifted_pair(ROW_A)
    res = parse_register_csv(_csv(head, ROW_B, ROW_C, tail))
    assert len(res.rows) == 2
    assert sorted(res.quarantine["kind"]) == ["continuation", "truncated"]
    assert set(res.quarantine["n_fields"]) == {22}


def test_shifted_22_field_fragments_adjacent_are_joined():
    head, tail = _shifted_pair(ROW_A)
    res = parse_register_csv(_csv(ROW_B, head, tail))
    assert res.quarantine.empty
    joined = res.rows[res.rows["repair"] == "join"].iloc[0]
    assert joined["Pris"] == "25,40" and joined["Status"] == "Aktuell"
    assert joined["record_id"].split(":")[0] == parse_register_csv(_csv(ROW_A)).rows.loc[0, "record_id"].split(":")[0]


def test_quoted_multiline_cell_is_normalized():
    row = ROW_A.replace("Testbolaget B", '"Testbolaget\nser. B"')
    res = parse_register_csv(_csv(row))
    assert len(res.rows) == 1
    assert res.rows.loc[0, "Instrumentnamn"] == "Testbolaget ser. B"
    assert res.rows.loc[0, "repair"] == "cell_break"
