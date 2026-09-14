"""Closed period MAR come attributo (ADR-022): giorni dall'ultimo report noto a `as_of`."""

from __future__ import annotations

import pandas as pd

# Gli emittenti quotati riportano almeno ogni sei mesi: se l'ultima data nota precede T di oltre
# MAX_REPORT_GAP_DAYS, la lista (Yahoo) e' incompleta e l'attributo va trattato come UNKNOWN (ADR-043).
MAX_REPORT_GAP_DAYS = 200


def effective_days(days: int | None) -> int | None:
    return None if days is None or days > MAX_REPORT_GAP_DAYS else days


def days_since_report(report_dates: pd.DatetimeIndex | None, as_of: pd.Timestamp) -> int | None:
    if report_dates is None or len(report_dates) == 0:
        return None
    past = report_dates[report_dates.normalize() <= as_of.normalize()]
    if len(past) == 0:
        return None
    return int((as_of.normalize() - past.max().normalize()).days)


def window_label(days: int | None, window_days: int) -> str:
    days = effective_days(days)
    if days is None:
        return "UNKNOWN"
    return "IN_POST_REPORT_WINDOW" if days <= window_days else "OUTSIDE"
