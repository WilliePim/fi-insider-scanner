"""Markdown tables with no dependency (no `tabulate`)."""

from __future__ import annotations

import math

import pandas as pd


def fmt(value, digits: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        if math.isnan(value):
            return "—"
        return f"{value:,.{digits}f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value).replace("|", "\\|")


def md_table(df: pd.DataFrame, digits: int = 2, index: bool = False) -> str:
    frame = df.reset_index() if index else df
    cols = [str(c) for c in frame.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for row in frame.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(v, digits) for v in row) + " |")
    return "\n".join(lines)
