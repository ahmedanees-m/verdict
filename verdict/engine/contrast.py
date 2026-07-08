"""Number-contrast harness: the same claim, the same model, two answers.

The unconstrained baseline and the VERDICT pipeline both answer the claim. The
harness reads the quantities out of each answer and asks one question of every
number: is it backed by a receipt? The baseline produces no receipts, so none of its
figures carry provenance; VERDICT emits a number only when it can name the file and
computation behind it. The contrast is provenance, not correctness -- the baseline may
well be right, but it cannot show its work, and VERDICT cannot state a number it cannot
show.

The annotation helpers are pure and are unit-tested offline. The `contrast` runner
makes the two Claude calls.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..validator import _fmt, _is_year, numbers_in
from . import baseline, pipeline


def _backed_set(receipts) -> set[str]:
    out = set()
    for g in receipts:
        if isinstance(g.value, (int, float)):
            out.add(_fmt(g.value))
    return out


def annotate(text: str, receipts) -> dict:
    """Split the quantities in `text` into those backed by a receipt and those not.

    Years are excluded as structural, matching the fabrication validator.
    """
    backed_values = _backed_set(receipts)
    numbers, backed, unbacked = [], [], []
    for n in numbers_in(text):
        if _is_year(n):
            continue
        numbers.append(n)
        (backed if _fmt(float(n)) in backed_values else unbacked).append(n)
    return {"numbers": numbers, "backed": backed, "unbacked": unbacked}


@dataclass
class ContrastReport:
    claim: str
    baseline_answer: str
    baseline_numbers: list[str] = field(default_factory=list)
    baseline_unbacked: list[str] = field(default_factory=list)
    verdict: str = ""
    verdict_narrative: str = ""
    verdict_numbers: list[str] = field(default_factory=list)
    verdict_unbacked: list[str] = field(default_factory=list)
    receipt_count: int = 0

    def summary(self) -> str:
        b, bu = len(self.baseline_numbers), len(self.baseline_unbacked)
        v, vu = len(self.verdict_numbers), len(self.verdict_unbacked)
        return (
            f"Baseline: {b} quantities, {bu} with no receipt "
            f"({'none provable' if bu == b else f'{b - bu} coincide with a receipt'}).  "
            f"VERDICT: {v} quantities, {vu} with no receipt "
            f"({self.receipt_count} receipts available)."
        )


def contrast(claim_text: str, store, *, result: "pipeline.EngineResult | None" = None) -> ContrastReport:
    """Run the baseline and VERDICT on the same claim and annotate both."""
    answer = baseline.ask_baseline(claim_text)
    result = result or pipeline.evaluate(claim_text, store)

    b = annotate(answer, result.receipts)
    v = annotate(result.narrative, result.receipts)
    return ContrastReport(
        claim=claim_text,
        baseline_answer=answer,
        baseline_numbers=b["numbers"], baseline_unbacked=b["unbacked"],
        verdict=result.verdict.value,
        verdict_narrative=result.narrative,
        verdict_numbers=v["numbers"], verdict_unbacked=v["unbacked"],
        receipt_count=len(result.receipts),
    )
