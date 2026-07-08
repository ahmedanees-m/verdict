"""Positive genetic-support evidence.

The confound library establishes what would make a claim fall over. A genetic-support
claim also needs a positive leg: a receipted, robust source that the target is
genetically supported for the disease. That leg is the Open Targets genetic-association
score, gathered here and handed to the composer. A SUPPORTED verdict on such a claim is
therefore computed from a receipted value above a fixed threshold, not retrieved as an
assertion, and it only stands when no confound check fires.
"""
from __future__ import annotations

from ..checks.base import Claim
from ..receipts import NO_RECEIPT, Gated

# Open Targets genetic-association score above which genetic support is established.
GENETIC_SUPPORT_MIN = 0.5


def gather_support(claim: Claim, store) -> list[Gated]:
    """Receipted positive evidence for a genetic-support claim; empty otherwise."""
    if claim.claim_type != "genetic_support" and claim.scope != "genetic_association":
        return []
    if not claim.gene:
        return []
    ot = store.opentargets(claim.gene)
    if ot is NO_RECEIPT:
        return []
    score = ot.get("genetic_association_score")
    if score is None or score is NO_RECEIPT:
        return []
    if isinstance(score.value, (int, float)) and score.value >= GENETIC_SUPPORT_MIN:
        return [score]
    return []
