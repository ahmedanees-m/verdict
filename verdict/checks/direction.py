"""Direction check: does knockdown move the program the way the claim implies?

A claim that a gene *promotes* a program predicts that knocking the gene down
*lowers* the program; a claim that it *represses* predicts the opposite. The
check compares the sign of the perturbation's aggregate effect on the program
gene set, in the claim's cell type and condition, against that prediction. An
opposite, well-powered effect fires (routing to REFUTED). It fires only when the
context matches the assay (CD4+ T) and the effect clears the power gate.
"""
from __future__ import annotations

import math

from .base import Claim, CheckResult, Status, CD4, CROSSGUIDE_MIN
from .programs import resolve_program_genes
from ..receipts import NO_RECEIPT

name = "direction"

# Direction verbs and the sign of the log fold change knockdown should produce
# on the program if the claim holds.
KNOCKDOWN_LOWERS = {"promotes", "promote", "required_for", "activates", "activate",
                    "induces", "induce", "drives", "drive", "positive_regulator"}
KNOCKDOWN_RAISES = {"represses", "repress", "inhibits", "inhibit", "suppresses",
                    "suppress", "negative_regulator", "antagonizes"}

DEFAULT_CONDITION = "Stim8hr"


def run(claim: Claim, store) -> CheckResult:
    if claim.cell_type not in CD4 and claim.scope != "organism_wide":
        return CheckResult(
            name, Status.INSUFFICIENT,
            f"Claim cell type {claim.cell_type!r} is not CD4+ T; direction not evaluable here "
            "(routes to range_scope).",
        )
    if not claim.gene:
        return CheckResult(name, Status.INSUFFICIENT, "No target gene on the claim.")

    direction = (claim.direction or "").lower()
    if direction in KNOCKDOWN_LOWERS:
        predicted_sign = -1.0
    elif direction in KNOCKDOWN_RAISES:
        predicted_sign = 1.0
    else:
        return CheckResult(name, Status.INSUFFICIENT,
                           f"Claim direction {claim.direction!r} is not a promote/repress relation.")

    genes = resolve_program_genes(claim)
    if not genes:
        return CheckResult(name, Status.INSUFFICIENT,
                           f"Program {claim.program!r} has no defined marker gene set.")

    condition = claim.condition or DEFAULT_CONDITION
    effect = store.zhu_effect(claim.gene, genes, condition)
    if effect is NO_RECEIPT:
        return CheckResult(name, Status.INSUFFICIENT,
                           f"No receipted effect of {claim.gene} knockdown on the "
                           f"{claim.program} program in {condition}.")

    mean_lfc = effect["mean_log_fc"].value
    n_genes = int(effect["n_genes"].value)
    n_sig = int(effect["n_significant"].value)
    evidence = [effect["mean_log_fc"], effect["n_significant"]]
    evidence += store.zhu_gene_effects(claim.gene, genes, condition)[:6]

    power = store.zhu_power(claim.gene, condition)
    crossguide = power.value if power is not NO_RECEIPT else None
    if power is not NO_RECEIPT:
        evidence.append(power)

    if crossguide is None or (isinstance(crossguide, float) and math.isnan(crossguide)):
        return CheckResult(name, Status.INSUFFICIENT,
                           f"Cross-guide concordance unavailable for {claim.gene} in {condition} "
                           "(single-guide or untested); direction not well-powered.", evidence)
    if crossguide < CROSSGUIDE_MIN or n_sig < 1:
        return CheckResult(
            name, Status.INSUFFICIENT,
            f"Underpowered: cross-guide r={crossguide:.2f} (min {CROSSGUIDE_MIN}), "
            f"{n_sig}/{n_genes} program genes significant.", evidence)

    observed_sign = 1.0 if mean_lfc > 0 else -1.0
    moved = "up" if mean_lfc > 0 else "down"
    if observed_sign != predicted_sign:
        return CheckResult(
            name, Status.FIRED,
            f"Knockdown of {claim.gene} moves the {claim.program} program {moved} "
            f"(mean log2FC {mean_lfc:+.3f}, {n_sig}/{n_genes} genes significant, "
            f"cross-guide r={crossguide:.2f}) in {condition} CD4+ T cells, opposite to the "
            f"claim that {claim.gene} {direction} it.", evidence)
    return CheckResult(
        name, Status.NOT_FIRED,
        f"Knockdown of {claim.gene} moves the {claim.program} program {moved} "
        f"(mean log2FC {mean_lfc:+.3f}, {n_sig}/{n_genes} genes significant) in {condition}, "
        f"consistent with the claim that {claim.gene} {direction} it.", evidence)
