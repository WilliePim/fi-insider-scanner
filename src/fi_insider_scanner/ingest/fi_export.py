"""Client incrementale per l'export CSV di FI (ADR-001). Solo per il caso zero.

Regole: un thread, pausa >= `pause_seconds` tra le richieste, massimo `max_requests` per run,
User-Agent identificabile, contatto solo da variabile d'ambiente FI_SCANNER_CONTACT.
L'export tronca in silenzio a `row_cap` righe: ogni finestra di pubblicazione con >= row_cap righe
viene dimezzata; un singolo giorno che raggiunge il tetto è un errore esplicito, mai un troncamento.
"""

from __future__ import annotations

import os
import time
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta

import pandas as pd

from .rawcsv import RawParseResult, parse_register_csv

INITIAL_WINDOW_DAYS = 10


class ExportCapError(RuntimeError):
    """Un singolo giorno di pubblicazione raggiunge il tetto dell'export FI."""


class RequestBudgetError(RuntimeError):
    """Superato il numero massimo di richieste per run."""


@dataclass
class FetchLog:
    requests: list[dict] = field(default_factory=list)

    def add(self, start: date, end: date, n_rows: int, seconds: float) -> None:
        self.requests.append({"from": str(start), "to": str(end), "rows": n_rows, "seconds": round(seconds, 2)})


def build_url(base_url: str, start: date, end: date) -> str:
    params = {
        "SearchFunctionType": "Insyn",
        "Utgivare": "",
        "PersonILedandeStällningNamn": "",
        "Transaktionsdatum.From": "",
        "Transaktionsdatum.To": "",
        "Publiceringsdatum.From": start.isoformat(),
        "Publiceringsdatum.To": end.isoformat(),
        "button": "export",
    }
    return base_url + "?" + urllib.parse.urlencode(params, encoding="utf-8")


def user_agent(base: str) -> str:
    contact = os.environ.get("FI_SCANNER_CONTACT", "").strip()
    return f"{base} {contact}".strip() if contact else base


class HttpFetcher:
    def __init__(self, base_url: str, ua: str, timeout: int = 60):
        self.base_url, self.ua, self.timeout = base_url, ua, timeout

    def __call__(self, start: date, end: date) -> bytes:
        req = urllib.request.Request(build_url(self.base_url, start, end), headers={"User-Agent": self.ua})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.read()


class FiExportClient:
    """`fetch(start, end) -> bytes` iniettabile per i test."""

    def __init__(self, fetch: Callable[[date, date], bytes], pause_seconds: float, max_requests: int, row_cap: int, sleep=time.sleep):
        self.fetch, self.pause, self.max_requests, self.row_cap, self.sleep = fetch, pause_seconds, max_requests, row_cap, sleep
        self.log = FetchLog()
        self._last: float | None = None

    def _get(self, start: date, end: date) -> RawParseResult:
        if len(self.log.requests) >= self.max_requests:
            raise RequestBudgetError(f"raggiunto il massimo di {self.max_requests} richieste")
        if self._last is not None:
            wait = self.pause - (time.monotonic() - self._last)
            if wait > 0:
                self.sleep(wait)
        t0 = time.monotonic()
        data = self.fetch(start, end)
        self._last = time.monotonic()
        parsed = parse_register_csv(data)
        self.log.add(start, end, parsed.physical_records, self._last - t0)
        return parsed

    def fetch_range(self, start: date, end: date) -> list[RawParseResult]:
        """Finestre iniziali di INITIAL_WINDOW_DAYS, dimezzate finché restano sotto il tetto."""
        out: list[RawParseResult] = []
        cursor = start
        while cursor <= end:
            stop = min(cursor + timedelta(days=INITIAL_WINDOW_DAYS - 1), end)
            out.extend(self._fetch_window(cursor, stop))
            cursor = stop + timedelta(days=1)
        return out

    def _fetch_window(self, start: date, end: date) -> list[RawParseResult]:
        parsed = self._get(start, end)
        if parsed.physical_records < self.row_cap:
            return [parsed]
        if start == end:
            raise ExportCapError(f"il giorno {start} ha >= {self.row_cap} righe: l'export FI le tronca")
        mid = start + (end - start) // 2
        return self._fetch_window(start, mid) + self._fetch_window(mid + timedelta(days=1), end)


def merge_window_replace(bulk_rows: pd.DataFrame, fi_rows: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """Le righe FI sostituiscono tutte le righe bulk con pubblicazione nella finestra [start, end]."""
    pub = pd.to_datetime(bulk_rows["Publiceringsdatum"], errors="coerce").dt.normalize()
    keep = bulk_rows[(pub < pd.Timestamp(start)) | (pub > pd.Timestamp(end)) | pub.isna()]
    merged = pd.concat([keep, fi_rows], ignore_index=True)
    return merged.drop_duplicates("record_id", keep="last").reset_index(drop=True)
