"""Shared interface for the confound library. Checks are pure + deterministic (no LLM)."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Protocol


class Status(str, Enum):
    FIRED = "FIRED"            # the confound is present
    NOT_FIRED = "NOT_FIRED"   # the confound is absent
    INSUFFICIENT = "INSUFFICIENT"  # not enough receipted data to decide


@dataclass
class Claim:
    text: str
    gene: Optional[str] = None
    variant: Optional[str] = None
    disease: Optional[str] = None
    program: Optional[str] = None
    program_genes: Optional[list[str]] = None
    direction: Optional[str] = None       # "promotes" | "represses" | "required_for" ...
    scope: Optional[str] = None           # "cell_type_specific" | "organism_wide" | "selective"
    cell_type: Optional[str] = None
    condition: Optional[str] = None       # "Rest" | "Stim8hr" | "Stim48hr"
    cited_source: Optional[str] = None    # dataset key for circularity, e.g. "Zhu2025"
    asserts_safety: bool = False
    claim_type: Optional[str] = None      # selectivity | safety | genetic_support | directional | composite


@dataclass
class CheckResult:
    check_name: str
    status: Status
    rationale: str
    evidence: list = field(default_factory=list)   # list[Gated]


class Check(Protocol):
    name: str

    def run(self, claim: Claim, store) -> CheckResult: ...


# calibratable defaults (several grounded in the atlas's own reported numbers)
FDR_SIG = 0.10          # the atlas uses FDR < 10%
CROSSGUIDE_MIN = 0.30   # atlas medians were ~0.49-0.52; require adequate concordance
CHRONOS_ESSENTIAL = -0.5  # DepMap Chronos; common-essential flag is the cleaner signal
BREADTH_TOP_DECILE = 0.90  # trans-effect breadth percentile for "broad"
CD4 = {"CD4+ T", "CD4 T", "CD4", "cd4", None}  # None/unspecified => CD4+ T is a valid test context
