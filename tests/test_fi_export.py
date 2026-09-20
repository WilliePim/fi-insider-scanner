from datetime import date

import pytest

from fi_insider_scanner.ingest.fi_export import (
    ExportCapError,
    FiExportClient,
    RequestBudgetError,
    build_url,
    merge_window_replace,
    user_agent,
)
from fi_insider_scanner.ingest.rawcsv import EXPECTED_HEADER, parse_register_csv

HEADER = ";".join(EXPECTED_HEADER) + ";"


def row(day: str, person: str = "Anna Svensson") -> str:
    return (
        f"{day} 10:00:00;Testbolaget AB;549300OQ8R5TCAP0BS18;{person};{person};VD;;;;Ja;;Förvärv;Aktie;Test B;"
        f"SE0000108656;{day} 00:00:00;100,0;Antal;10,0;SEK;NASDAQ STOCKHOLM AB;Aktuell;"
    )


def export_bytes(rows: list[str]) -> bytes:
    return ("\r\n".join([HEADER, *rows]) + "\r\n").encode("utf-16-le")


class FakeFI:
    """Registro finto: `per_day` righe per giorno; registra le chiamate."""

    def __init__(self, per_day: dict[str, int]):
        self.per_day, self.calls = per_day, []

    def __call__(self, start: date, end: date) -> bytes:
        self.calls.append((start, end))
        rows = []
        d = start
        while d <= end:
            rows += [row(d.isoformat(), f"P{i} X") for i in range(self.per_day.get(d.isoformat(), 0))]
            d = d.fromordinal(d.toordinal() + 1)
        return export_bytes(rows)


def test_url_and_user_agent(monkeypatch):
    url = build_url("https://example/Search", date(2026, 6, 1), date(2026, 6, 10))
    assert "SearchFunctionType=Insyn" in url and "Publiceringsdatum.From=2026-06-01" in url and "button=export" in url
    monkeypatch.delenv("FI_SCANNER_CONTACT", raising=False)
    assert user_agent("fi-insider-scanner/0.1 (research)") == "fi-insider-scanner/0.1 (research)"
    monkeypatch.setenv("FI_SCANNER_CONTACT", "mail@example.org")
    assert user_agent("fi-insider-scanner/0.1 (research)").endswith("mail@example.org")


def test_windows_split_below_cap_and_pause_is_sequential():
    per_day = {f"2026-06-{d:02d}": 300 for d in range(1, 11)}  # 3.000 righe in 10 giorni
    fake = FakeFI(per_day)
    sleeps = []
    client = FiExportClient(fake, pause_seconds=5.0, max_requests=20, row_cap=1000, sleep=sleeps.append)
    parts = client.fetch_range(date(2026, 6, 1), date(2026, 6, 10))
    total = sum(len(p.rows) for p in parts)
    assert total == 3000
    assert all(p.physical_records < 1000 for p in parts)
    # 10 giorni -> 5+5 (1500, tetto) -> 3+2 / 2+3 (900, 600, 600, 900): 1 + 2 + 4 = 7 richieste, sequenziali
    assert len(fake.calls) == 7
    assert len(sleeps) == len(fake.calls) - 1 and all(s <= 5.0 for s in sleeps)


def test_single_day_at_cap_raises():
    fake = FakeFI({"2026-06-01": 1000})
    client = FiExportClient(fake, pause_seconds=0.0, max_requests=20, row_cap=1000, sleep=lambda s: None)
    with pytest.raises(ExportCapError):
        client.fetch_range(date(2026, 6, 1), date(2026, 6, 1))


def test_request_budget():
    fake = FakeFI({})
    client = FiExportClient(fake, pause_seconds=0.0, max_requests=2, row_cap=1000, sleep=lambda s: None)
    with pytest.raises(RequestBudgetError):
        client.fetch_range(date(2026, 6, 1), date(2026, 7, 31))


def test_merge_window_replace():
    bulk = parse_register_csv(
        ("\r\n".join([HEADER, row("2026-05-01"), row("2026-06-05"), row("2026-06-20")]) + "\r\n").encode("utf-16-le")
    ).rows
    fi = parse_register_csv(export_bytes([row("2026-06-05", "Erik Berg"), row("2026-06-06")])).rows
    merged = merge_window_replace(bulk, fi, date(2026, 6, 1), date(2026, 6, 10))
    days = sorted(merged["Publiceringsdatum"].str.slice(0, 10))
    assert days == ["2026-05-01", "2026-06-05", "2026-06-06", "2026-06-20"]
    assert "Erik Berg" in set(merged["Person i ledande ställning"])
