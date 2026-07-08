"""Selectivity is not safety.

A claim that a target is *safe* because its action is restricted to activated
CD4+ T cells conflates two things: where the effect is measured (CD4+ T, which
the assay can speak to) and whether the target is safe across the immune system
(which CD4-only data cannot establish). When a claim carries an organism-wide
safety assertion anchored to a CD4-tested target, the check fires as
scope-restricted, and broad expression (GTEx/HPA) or Open Targets safety
liabilities strengthen it. The engine never emits an organism-wide safe verdict.
"""
from __future__ import annotations

from .base import Claim, CheckResult, Status, CD4
from ..receipts import NO_RECEIPT

name = "selectivity_safety"

# Fraction of surveyed tissues above which expression counts as broad.
BROAD_TISSUE_FRACTION = 0.5


def run(claim: Claim, store) -> CheckResult:
    if not claim.asserts_safety or claim.scope not in {"organism_wide", "selective"}:
        return CheckResult(name, Status.NOT_FIRED, "No organism-wide safety assertion to test.")
    if not claim.gene or claim.cell_type not in CD4:
        return CheckResult(name, Status.INSUFFICIENT,
                           "No CD4-anchored target to assess; organism-wide safety not evaluable "
                           "from this data.")

    reasons: list[str] = []
    evidence = []
    if claim.scope == "organism_wide":
        reasons.append("an organism-wide safety claim cannot be established from CD4+ T-cell data")

    breadth = store.expression_breadth(claim.gene)
    if breadth is not NO_RECEIPT and isinstance(breadth.value, (int, float)) \
            and breadth.value >= BROAD_TISSUE_FRACTION:
        reasons.append(f"{claim.gene} is broadly expressed across tissues (breadth {breadth.value:.2f})")
        evidence.append(breadth)

    ot = store.opentargets(claim.gene)
    if ot is not NO_RECEIPT:
        liabilities = ot.get("safety_liabilities")
        if liabilities is not None and liabilities.value:
            reasons.append(f"{claim.gene} carries {int(liabilities.value)} Open Targets safety liabilities")
            evidence.append(liabilities)

    if reasons:
        return CheckResult(
            name, Status.FIRED,
            f"The safety claim for {claim.gene} is scope-restricted: " + "; ".join(reasons) + ".",
            evidence)
    return CheckResult(name, Status.NOT_FIRED,
                       f"No scope-restriction confound detected for the {claim.gene} safety claim.",
                       evidence)
