"""Essentiality / pleiotropy: a 'selective' claim confounded by broad essentiality.

Fires when a claim asserts that a gene *selectively* regulates a program yet the
gene is broadly essential (DepMap) and its knockdown perturbs a top-decile
breadth of the transcriptome (Zhu). The finding is that the *selectivity* is
unsupported, not that the effect is an artifact and not that the gene fails to
regulate the program.
"""
from __future__ import annotations

from .base import Claim, CheckResult, Status, CHRONOS_ESSENTIAL, BREADTH_TOP_DECILE
from .direction import DEFAULT_CONDITION
from ..receipts import NO_RECEIPT

name = "essentiality"


def run(claim: Claim, store) -> CheckResult:
    if claim.scope != "selective":
        return CheckResult(name, Status.NOT_FIRED,
                           "Claim does not assert selectivity; pleiotropy confound not applicable.")
    if not claim.gene:
        return CheckResult(name, Status.INSUFFICIENT, "No target gene on the claim.")

    essentiality = store.depmap_essentiality(claim.gene)
    condition = claim.condition or DEFAULT_CONDITION
    breadth = store.zhu_breadth(claim.gene, condition)
    if essentiality is NO_RECEIPT or breadth is NO_RECEIPT:
        return CheckResult(name, Status.INSUFFICIENT,
                           f"Essentiality (DepMap) or trans-effect breadth (Zhu) unavailable "
                           f"for {claim.gene}.")

    common = essentiality.get("common_essential")
    chronos = essentiality.get("chronos_median")
    frac = essentiality.get("frac_dependent")
    evidence = [g for g in (chronos, frac, common, breadth) if g is not None]

    is_essential = bool(common and common.value) or (
        chronos is not None and chronos.value < CHRONOS_ESSENTIAL)
    is_broad = breadth.value >= BREADTH_TOP_DECILE

    if is_essential and is_broad:
        pct = breadth.value * 100
        if common is not None and common.value:
            ess_txt = (f"is common-essential in DepMap (dependent in "
                       f"{frac.value * 100:.0f}% of cell lines)" if frac is not None
                       else "is common-essential in DepMap")
        else:
            ess_txt = f"is broadly essential in DepMap (median Chronos {chronos.value:.2f})"
        return CheckResult(
            name, Status.FIRED,
            f"The claim's selectivity is not supported: knockdown of {claim.gene} drives a "
            f"genome-wide transcriptional response ({pct:.0f}th-percentile breadth in {condition} "
            f"CD4+ T cells) and {claim.gene} {ess_txt}. A broadly essential gene reads as a "
            f"specific regulator here only as an essentiality artifact, and is a poor target on "
            f"its own.", evidence)
    return CheckResult(
        name, Status.NOT_FIRED,
        f"No pleiotropy/essentiality confound for {claim.gene}: it is not both broadly essential "
        f"and broadly pleiotropic in this data.", evidence)
