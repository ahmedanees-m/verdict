"""Run the pre-registered EVAL_SET against the store and report the matrix."""
from __future__ import annotations

from collections import Counter

import yaml

from verdict.store import Store
from verdict.checks.base import Claim, Status
from verdict.checks.registry import CHECKS
from verdict.compose.composer import compose
from verdict.compose.support import gather_support


def claim_of(case: dict) -> Claim:
    p = case.get("parsed", {}) or {}
    return Claim(
        text=case.get("claim", ""), gene=p.get("gene"), variant=p.get("variant"),
        disease=p.get("disease"), program=p.get("program"), direction=p.get("direction"),
        scope=p.get("scope"), cell_type=p.get("cell_type"), condition=p.get("condition"),
        cited_source=p.get("cited_source"),
        asserts_safety=(case.get("claim_type") == "safety"),
        claim_type=case.get("claim_type"))


def main() -> None:
    cases = yaml.safe_load(open("EVAL_SET.yaml"))["cases"]
    store = Store()
    matrix: Counter = Counter()
    print(f"{'':2s} {'case':24s} {'expected':12s} {'actual':12s} fired")
    for case in cases:
        claim = claim_of(case)
        results = [run(claim, store) for run in CHECKS.values()]
        verdict, _ = compose(results, support=gather_support(claim, store))
        fired = [r.check_name for r in results if r.status is Status.FIRED]
        expected = case["expected_verdict"]
        ok = verdict.value == expected
        matrix[(expected, verdict.value)] += 1
        print(f"{'OK' if ok else 'XX'} {case['id']:24s} {expected:12s} {verdict.value:12s} {fired}")
    correct = sum(v for (e, a), v in matrix.items() if e == a)
    print(f"\naccuracy: {correct}/{sum(matrix.values())}")
    print("confusion (expected -> actual):")
    for (e, a), v in sorted(matrix.items()):
        print(f"  {e} -> {a}: {v}")


if __name__ == "__main__":
    main()
