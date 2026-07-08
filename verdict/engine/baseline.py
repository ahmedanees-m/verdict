"""Adversarial baseline: the same claim through unconstrained Claude.

The same question, put to the same model with no store, no gate, and no receipts.
The prompt is deliberately fair -- it asks for an ordinary expert assessment, not for
fabrication. That is the point of the contrast: a capable model answering honestly
still produces specific figures (effect sizes, essentiality scores, association
scores) with no way to attach provenance to any of them. VERDICT answers the same
question with every number receipted. The asymmetry is provenance, not correctness.
"""
from __future__ import annotations

from . import client

_SYSTEM = (
    "You are a computational immunologist assessing a drug-target claim. Give a direct, "
    "substantiated assessment in four to six sentences: state whether the claim holds, and "
    "cite the specific quantitative evidence a specialist would point to (effect sizes, "
    "essentiality or dependency scores, genetic-association scores, expression breadth) with "
    "concrete numbers where you can. Write as you normally would for an expert reader."
)


def ask_baseline(claim_text: str) -> str:
    """Unconstrained Claude's raw answer to the claim (no receipts, no gate)."""
    return client.reason(_SYSTEM, f"Claim: {claim_text!r}", effort="medium", max_tokens=2000)
