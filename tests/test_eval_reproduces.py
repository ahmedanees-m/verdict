"""The committed sample store reproduces the pre-registered verdict matrix, so the
evaluation runs end to end from a clean clone without the multi-gigabyte atlas."""
import yaml

from verdict.store import Store
from verdict.checks.registry import CHECKS
from verdict.compose.composer import compose
from verdict.compose.support import gather_support
from scripts.run_eval import claim_of


def test_sample_store_reproduces_eval_matrix():
    store = Store("data/sample_store")
    cases = yaml.safe_load(open("EVAL_SET.yaml"))["cases"]
    assert cases, "EVAL_SET.yaml has no cases"
    for case in cases:
        claim = claim_of(case)
        results = [run(claim, store) for run in CHECKS.values()]
        verdict, _ = compose(results, support=gather_support(claim, store))
        assert verdict.value == case["expected_verdict"], (
            f"{case['id']}: expected {case['expected_verdict']}, got {verdict.value}")
