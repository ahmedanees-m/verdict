"""Adversarial baseline -- the SAME claim through unconstrained Claude: no store,
no gate, no receipts. Captured for the side-by-side. This is the verifier/adversarial
pattern. Keep the prompt FAIR (same question, no sabotage): the win is the asymmetry
that only VERDICT can produce a receipted number, not forcing the baseline to lie.
"""
from __future__ import annotations


def ask_baseline(question: str) -> str:
    """TODO(Step 5): call unconstrained Claude and return its raw answer."""
    raise NotImplementedError("Wire to an unconstrained Claude call in Step 5.")
