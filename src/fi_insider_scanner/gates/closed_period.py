"""Closed period MAR come attributo (ADR-022): giorni dall'ultimo report noto a `as_of`."""

from __future__ import annotations

import pandas as pd


def days_since_report(report_dates: pd.DatetimeIndex | None, as_of: pd.Timestamp) -> int | None:
    if report_dates is None or len(report_dates) == 0:
        return None
    past = report_dates[report_dates.normalize() <= as_of.normalize()]
    if len(past) == 0:
        return None
    return int((as_of.normalize() - past.max().normalize()).days)


def window_label(days: int | None, window_days: int) -> str:
    if days is None:
        return "UNKNOWN"
    return "IN_POST_REPORT_WINDOW" if days <= window_days else "OUTSIDE"
