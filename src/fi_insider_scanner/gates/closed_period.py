"""MAR closed period as an attribute (ADR-022): days from the last known report to `as_of`."""

from __future__ import annotations

import pandas as pd

# a listed issuer reports at least every six months: when the last known date precedes T by more than
# MAX_REPORT_GAP_DAYS the (Yahoo) list is incomplete and the attribute must be treated as UNKNOWN (ADR-043)
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
