"""Caricamento del registro canonico con valori FX, pronto per gate ed eventi."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from . import store
from .canon.visibility import Register
from .market import fx as fxmod


@lru_cache(maxsize=1)
def canonical_with_values() -> pd.DataFrame:
    df = store.load_frame("transactions")
    return fxmod.attach_values(df, fxmod.load_fx())


@lru_cache(maxsize=4)
def register(mode: str = "snapshot", timing: str = "pub") -> Register:
    return Register(canonical_with_values(), store.load_rules(), mode=mode, timing=timing)
