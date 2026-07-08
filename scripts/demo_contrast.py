"""Number-contrast demo: the same claim, the same model, two answers.

For each claim it prints the unconstrained baseline (no store, no receipts) and the
VERDICT answer (every number receipted), the quantities each states, and which of
those quantities carry no provenance. The reasoning trace is printed so the Claude
decisions are legible. Pass claims as arguments to run your own.
"""
from __future__ import annotations

import sys

from verdict.store import Store
from verdict.engine import pipeline
from verdict.engine.contrast import contrast

HERO = [
    "MED12 is a selective regulator of the T-cell effector program in CD4+ T cells.",
    "GATA3 promotes the Th2 program in CD4+ T cells.",
    "TYK2 is a genetically supported target for psoriasis.",
]

RULE = "=" * 78
THIN = "-" * 78


def one(claim: str, store) -> None:
    result = pipeline.evaluate(claim, store)
    rep = contrast(claim, store, result=result)

    print(RULE)
    print(f"CLAIM: {claim}")
    print(THIN)
    print("UNCONSTRAINED BASELINE (no store, no receipts):")
    print(rep.baseline_answer)
    print(f"  quantities stated:        {rep.baseline_numbers}")
    print(f"  quantities with no receipt: {rep.baseline_unbacked}")
    print(THIN)
    print(f"VERDICT: {rep.verdict}")
    print(rep.verdict_narrative)
    print(f"  quantities stated:        {rep.verdict_numbers}")
    print(f"  quantities with no receipt: {rep.verdict_unbacked}  "
          f"(receipts available: {rep.receipt_count})")
    print(THIN)
    print("REASONING TRACE:")
    print(result.trace.as_markdown())
    print(THIN)
    print("NEXT EXPERIMENT (heuristic):")
    print(result.next_experiment)
    print(THIN)
    print(rep.summary())
    print()


def main() -> None:
    claims = sys.argv[1:] or HERO
    store = Store()
    for c in claims:
        one(c, store)


if __name__ == "__main__":
    main()
