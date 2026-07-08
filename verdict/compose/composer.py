"""Verdict composer: the deterministic precedence truth table.

    direction FIRED or circularity FIRED            -> REFUTED
    essentiality/selectivity_safety/range_scope FIRED -> OVERCLAIMED
    required input INSUFFICIENT / core unevaluable   -> INSUFFICIENT
    all relevant NOT_FIRED with receipted support    -> SUPPORTED

SUPPORTED requires receipted evidence (computed), never retrieval.
"""
from __future__ import annotations
from enum import Enum
from ..checks.base import CheckResult, Status


class Verdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    OVERCLAIMED = "OVERCLAIMED"
    REFUTED = "REFUTED"
    INSUFFICIENT = "INSUFFICIENT"


REFUTE_LEVEL = {"direction", "circularity"}
OVERCLAIM_LEVEL = {"essentiality", "selectivity_safety", "range_scope"}


def compose(results: list[CheckResult], *, support: list | None = None,
            core_evaluable: bool = True) -> tuple[Verdict, str]:
    fired = {r.check_name for r in results if r.status is Status.FIRED}
    any_not_fired_with_evidence = any(
        r.status is Status.NOT_FIRED and r.evidence for r in results
    )
    support = support or []

    if fired & REFUTE_LEVEL:
        return Verdict.REFUTED, f"Refute-level check fired: {sorted(fired & REFUTE_LEVEL)}"
    if fired & OVERCLAIM_LEVEL:
        return Verdict.OVERCLAIMED, f"Overclaim-level check fired: {sorted(fired & OVERCLAIM_LEVEL)}"
    if not core_evaluable:
        return Verdict.INSUFFICIENT, "Core claim not evaluable from receipted data."
    if support:
        return Verdict.SUPPORTED, "Receipted genetic-support evidence with no confound firing."
    if any_not_fired_with_evidence:
        return Verdict.SUPPORTED, "All relevant checks passed with receipted support."
    return Verdict.INSUFFICIENT, "No receipted evidence supports a positive verdict."
