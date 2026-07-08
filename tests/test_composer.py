from verdict.checks.base import CheckResult, Status
from verdict.compose.composer import compose, Verdict
from tests.helpers import gated


def r(name, status, evidence=None):
    return CheckResult(name, status, "test", evidence or [])


def test_direction_fired_gives_refuted():
    v, _ = compose([r("direction", Status.FIRED)])
    assert v is Verdict.REFUTED


def test_circularity_fired_gives_refuted():
    v, _ = compose([r("circularity", Status.FIRED)])
    assert v is Verdict.REFUTED


def test_selectivity_fired_gives_overclaimed():
    v, _ = compose([r("selectivity_safety", Status.FIRED)])
    assert v is Verdict.OVERCLAIMED


def test_refute_beats_overclaim_precedence():
    v, _ = compose([r("direction", Status.FIRED), r("range_scope", Status.FIRED)])
    assert v is Verdict.REFUTED


def test_supported_requires_receipted_evidence():
    # NOT_FIRED but with NO evidence -> INSUFFICIENT, never SUPPORTED (no retrieval)
    v, _ = compose([r("direction", Status.NOT_FIRED)])
    assert v is Verdict.INSUFFICIENT
    v2, _ = compose([r("direction", Status.NOT_FIRED, evidence=[gated(0.4)])])
    assert v2 is Verdict.SUPPORTED


def test_unevaluable_core_gives_insufficient():
    v, _ = compose([r("direction", Status.INSUFFICIENT)], core_evaluable=False)
    assert v is Verdict.INSUFFICIENT
