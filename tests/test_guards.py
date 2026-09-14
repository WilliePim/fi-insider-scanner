"""Guardie strutturali: isolamento dal resto del Desktop, niente informazione
futura nei moduli che decidono, niente linguaggio da raccomandazione."""

from __future__ import annotations

import ast
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "fi_insider_scanner"

FORBIDDEN_MODULES = ("form4_scanner", "invest_system", "compounder_watch", "edgar_llm")
FORBIDDEN_PATH_FRAGMENTS = ("form4-scanner", "invest-system", "compounder-watch")
DECIDING_PACKAGES = ("gates", "backtest/events.py", "backtest/control.py")
BANNED_WORDS = re.compile(
    r"raccomand|consigli|\bcompra\b|\bvendi\b|recommend|target price|köprekommendation|"
    r"opportunit|promettente|should buy",
    re.IGNORECASE,
)


def _py_files():
    return sorted(SRC.rglob("*.py"))


def test_no_imports_from_other_repos():
    for path in _py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                assert not name.startswith(FORBIDDEN_MODULES), f"{path}: import {name}"


def test_no_paths_to_other_repos_and_no_sys_path_mutation():
    for path in _py_files():
        text = path.read_text(encoding="utf-8")
        for frag in FORBIDDEN_PATH_FRAGMENTS:
            assert frag not in text, f"{path}: riferimento a {frag}"
        assert "sys.path.insert" not in text and "sys.path.append" not in text, path


def _deciding_files():
    for rel in DECIDING_PACKAGES:
        p = SRC / rel
        if p.is_dir():
            yield from sorted(p.rglob("*.py"))
        elif p.exists():
            yield p


def test_expost_fields_never_used_in_deciding_modules():
    for path in _deciding_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id.startswith("expost_"):
                raise AssertionError(f"{path}: usa {node.id}")
            if isinstance(node, ast.Attribute) and node.attr.startswith("expost_"):
                raise AssertionError(f"{path}: usa {node.attr}")
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.startswith("expost_"):
                raise AssertionError(f"{path}: usa la colonna {node.value}")


def test_deciding_modules_read_register_only_through_visibility():
    for path in _deciding_files():
        text = path.read_text(encoding="utf-8")
        for forbidden in ("read_sql", "sqlite3", "status_raw", "is_current", "chain_status", "superseded_at"):
            assert forbidden not in text, f"{path}: accesso diretto ({forbidden}); usare visibility.visible()"


def test_no_recommendation_vocabulary_in_templates():
    for path in list((SRC / "dossier").rglob("*.py")) + list((SRC / "backtest").rglob("report.py")):
        text = path.read_text(encoding="utf-8")
        m = BANNED_WORDS.search(text)
        assert m is None, f"{path}: vocabolario vietato '{m.group(0)}'"
