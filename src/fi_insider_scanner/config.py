"""Percorsi del repo e caricamento di config/pipeline.toml."""

from __future__ import annotations

import hashlib
import tomllib
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = REPO_ROOT / "config" / "pipeline.toml"
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CACHE_DIR = DATA_DIR / "cache"
DB_PATH = DATA_DIR / "fi.sqlite"
BACKTEST_DIR = REPO_ROOT / "backtest"
DOSSIER_DIR = REPO_ROOT / "dossier"


@lru_cache(maxsize=1)
def load() -> dict:
    with CONFIG_PATH.open("rb") as f:
        return tomllib.load(f)


def config_sha256() -> str:
    return hashlib.sha256(CONFIG_PATH.read_bytes()).hexdigest()
