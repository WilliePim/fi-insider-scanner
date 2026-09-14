"""Criteri di verdetto pre-registrati (ADR-035). Nessuna interpretazione oltre questi."""

from __future__ import annotations

from dataclasses import dataclass, field

from .stats import Summary

T_THRESHOLD = 2.0
US_EFFECT = 0.035


@dataclass
class Verdict:
    label: str
    reasons: list[str] = field(default_factory=list)
    checks: dict = field(default_factory=dict)


def _t_ok(t: float | None) -> bool:
    return t is not None and t >= T_THRESHOLD


def decide(primary: Summary, control: Summary | None, s0_mean: float | None, coverage: float, min_coverage: float) -> Verdict:
    checks = {
        "copertura": coverage,
        "copertura_minima": min_coverage,
        "P_media_positiva": primary.mean is not None and primary.mean > 0,
        "P_t_cr1_emittente_ge_2": _t_ok(primary.t_cr1_issuer),
        "C_media_positiva": control is not None and control.mean is not None and control.mean > 0,
        "C_t_cr1_emittente_ge_2": control is not None and _t_ok(control.t_cr1_issuer),
        "segno_invariato_S0": s0_mean is not None and primary.mean is not None and (s0_mean > 0) == (primary.mean > 0),
        "C_media_le_0": control is not None and control.mean is not None and control.mean <= 0,
        "MDE_le_3_5": primary.mde is not None and primary.mde <= US_EFFECT,
        "CI_P_include_0": primary.ci_low is not None and primary.ci_high is not None and primary.ci_low <= 0 <= primary.ci_high,
    }
    if coverage < min_coverage:
        return Verdict("INCONCLUSIVO", [f"copertura {coverage:.1%} sotto la soglia {min_coverage:.0%}"], checks)
    regge = checks["P_media_positiva"] and checks["P_t_cr1_emittente_ge_2"] and checks["C_media_positiva"] and checks["C_t_cr1_emittente_ge_2"] and checks["segno_invariato_S0"]
    if regge:
        return Verdict("REGGE", ["tutti i criteri REGGE soddisfatti"], checks)
    reasons = []
    if checks["C_media_le_0"]:
        reasons.append("matched control con media <= 0")
    if checks["MDE_le_3_5"] and checks["CI_P_include_0"]:
        reasons.append("MDE <= 3,5% e CI 95% di P include 0")
    if reasons:
        return Verdict("NON REGGE", reasons, checks)
    failed = [k for k in ("P_media_positiva", "P_t_cr1_emittente_ge_2", "C_media_positiva", "C_t_cr1_emittente_ge_2", "segno_invariato_S0") if not checks[k]]
    return Verdict("INCONCLUSIVO", [f"criterio REGGE non soddisfatto: {k}" for k in failed], checks)
