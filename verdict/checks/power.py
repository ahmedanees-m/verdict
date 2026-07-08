"""Power / support: is the perturbation behind the claim well-powered?

Reports cross-guide concordance and cell count for the perturbation and flags
weak support. This is a modifier: it annotates a verdict rather than setting one,
so it is not part of the composer precedence.
"""
from __future__ import annotations

import math

from .base import Claim, CheckResult, Status, CD4, CROSSGUIDE_MIN
from .direction import DEFAULT_CONDITION
from ..receipts import NO_RECEIPT

name = "power"

MIN_CELLS = 25


def run(claim: Claim, store) -> CheckResult:
    if claim.claim_type == "genetic_support" or claim.scope == "genetic_association":
        return CheckResult(name, Status.INSUFFICIENT,
                           "Claim rests on genetic association, not a perturbation; "
                           "perturbation power does not apply.")
    if not claim.gene or claim.cell_type not in CD4:
        return CheckResult(name, Status.INSUFFICIENT,
                           "No CD4-anchored perturbation to assess power for.")
    condition = claim.condition or DEFAULT_CONDITION
    summary = store.zhu_summary(claim.gene, condition)
    if summary is NO_RECEIPT:
        return CheckResult(name, Status.INSUFFICIENT,
                           f"No power statistics for {claim.gene} in {condition}.")

    evidence = []
    crossguide = None
    if "guide_correlation_signif" in summary:
        evidence.append(summary["guide_correlation_signif"])
        crossguide = summary["guide_correlation_signif"].value
    n_cells = None
    if "n_cells_target" in summary:
        evidence.append(summary["n_cells_target"])
        n_cells = summary["n_cells_target"].value

    weak = []
    if crossguide is None or (isinstance(crossguide, float) and math.isnan(crossguide)):
        weak.append("cross-guide concordance unavailable (single-guide or untested)")
    elif crossguide < CROSSGUIDE_MIN:
        weak.append(f"cross-guide r={crossguide:.2f} below {CROSSGUIDE_MIN}")
    if n_cells is not None and n_cells < MIN_CELLS:
        weak.append(f"only {int(n_cells)} targeting cells (min {MIN_CELLS})")

    if weak:
        return CheckResult(name, Status.FIRED,
                           f"Weak support for {claim.gene} in {condition}: " + "; ".join(weak),
                           evidence)
    detail = f"cross-guide r={crossguide:.2f}" if crossguide is not None else "concordance reported"
    return CheckResult(name, Status.NOT_FIRED,
                       f"Adequate support for {claim.gene} in {condition} ({detail}).", evidence)
