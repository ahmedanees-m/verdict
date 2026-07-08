"""Range / scope mismatch: claimed scope versus what the assay measured.

The assay measures the CD4+ T-cell transcriptome under three conditions. A claim
whose context lies entirely outside that (a different cell type, the whole immune
system) is not evaluable from this data and returns INSUFFICIENT, driving a
refusal. A claim anchored in the CD4+ T context but reaching to organism-wide
scope exceeds the assay and fires, routing to OVERCLAIMED.
"""
from __future__ import annotations

from .base import Claim, CheckResult, Status, CD4

name = "range_scope"

ASSAY_SCOPE = {"cell_types": {"CD4+ T"}, "readout": "transcriptomic",
               "conditions": {"Rest", "Stim8hr", "Stim48hr"}, "outcome_level": "molecular"}


def run(claim: Claim, store) -> CheckResult:
    if claim.cell_type not in CD4:
        return CheckResult(
            name, Status.INSUFFICIENT,
            f"Claim context ({claim.cell_type}) lies outside the CD4+ T assay; "
            "not evaluable from this data.")
    if claim.scope == "organism_wide":
        return CheckResult(
            name, Status.FIRED,
            "Organism-wide scope exceeds the CD4+ T-cell molecular readout of the assay.")
    return CheckResult(name, Status.NOT_FIRED, "Claim scope is within the assay scope.")
