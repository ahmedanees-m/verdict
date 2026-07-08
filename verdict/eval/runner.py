"""Run the pre-registered cases and report a confusion matrix.

Until the checks are wired to data (Steps 1/3), most cases return INSUFFICIENT --
which is honest. Once wired, this produces the matrix reported in the submission.
"""
from __future__ import annotations
from collections import Counter
from ..checks.base import Claim
from ..checks.registry import CHECKS
from ..compose.composer import compose, Verdict


def _claim_from_case(c: dict) -> Claim:
    p = c.get("parsed", {}) or {}
    return Claim(
        text=c.get("claim", ""),
        gene=p.get("gene"), variant=p.get("variant"), disease=p.get("disease"),
        program=p.get("program"), direction=p.get("direction"), scope=p.get("scope"),
        cell_type=p.get("cell_type"), condition=p.get("condition"),
        cited_source=p.get("cited_source"),
        asserts_safety=(c.get("claim_type") == "safety"),
    )


def run_case(case: dict, store) -> Verdict:
    claim = _claim_from_case(case)
    results = [run(claim, store) for run in CHECKS.values()]
    verdict, _ = compose(results)
    return verdict


def confusion(cases: list[dict], store) -> Counter:
    """Returns Counter[(expected, actual)]. Fill/skip TEMPLATE_FILL cases as needed."""
    matrix: Counter = Counter()
    for c in cases:
        if c.get("status") == "TEMPLATE_FILL":
            continue
        expected = c.get("expected_verdict", "UNKNOWN")
        actual = run_case(c, store).value
        matrix[(expected, actual)] += 1
    return matrix
