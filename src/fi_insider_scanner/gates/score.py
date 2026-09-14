"""Score Layer 1 (ADR-023): somma booleana 0-4, S3 forza 0. Nessun verdetto."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Layer1:
    cluster: bool
    not_routine: bool
    dilution_ok: bool
    no_large_holder: bool
    structural_s3: bool

    @property
    def score(self) -> int:
        if self.structural_s3:
            return 0
        return int(self.cluster) + int(self.not_routine) + int(self.dilution_ok) + int(self.no_large_holder)
