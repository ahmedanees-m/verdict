"""Offline tests for the reasoning layer: the parts that decide provenance without
calling Claude. The Claude-calling steps (parse, select, adjudicate, design, baseline)
are exercised by scripts/demo_contrast.py against the live model."""
import pytest

from verdict.checks.base import Claim
from verdict.compose.composer import Verdict, compose
from verdict.compose.support import gather_support
from verdict.engine.contrast import annotate
from verdict.validator import FabricationError, validate_output
from verdict.receipts import NO_RECEIPT
from tests.helpers import gated


# ---- the fabrication validator distinguishes quantities from nomenclature ----

def test_identifiers_are_not_quantities():
    # gene/program/variant/cell-type identifiers carry digits but assert no measurement
    assert validate_output("CD4+ Th17 cells, TYK2 P1104A, rsID rs34536443, DepMap 26Q1",
                           [], strict=False) == []


def test_hyphen_and_slash_joined_identifiers_are_not_quantities():
    # IL-4 / CDK8/19 join a letter to a digit; the digit is nomenclature, not a measurement
    assert validate_output("IL-4, IL-5, IL-13 via the CDK8/19 module", [], strict=False) == []
    # a genuine negative quantity is still caught
    assert validate_output("mean effect -4.5", [], strict=False) == ["-4.5"]


def test_bare_quantity_without_receipt_is_flagged():
    assert validate_output("breadth 0.75 and FDR 0.007", [gated(0.75)], strict=False) == ["0.007"]
    with pytest.raises(FabricationError):
        validate_output("breadth 0.75 and FDR 0.007", [gated(0.75)], strict=True)


def test_year_is_a_structural_allowance():
    assert validate_output("in 2025 the score was 0.93", [gated(0.93)], strict=False) == []


def test_ordinal_number_is_still_a_quantity():
    assert validate_output("in the top 99.9th percentile", [], strict=False) == ["99.9"]


# ---- the contrast annotator splits backed from unbacked ----

def test_annotate_backed_and_unbacked():
    receipts = [gated(0.93), gated(-0.54)]
    a = annotate("association 0.93, Chronos -0.54, and an invented 0.71 in CD4+ Th2", receipts)
    assert a["numbers"] == ["0.93", "-0.54", "0.71"]
    assert a["backed"] == ["0.93", "-0.54"]
    assert a["unbacked"] == ["0.71"]


# ---- the genetic-support leg and its composer path ----

class _StubStore:
    def __init__(self, score):
        self._score = score

    def opentargets(self, gene):
        if self._score is None:
            return NO_RECEIPT
        return {"genetic_association_score": gated(self._score)}


def _genetic_claim():
    return Claim(text="TYK2 is genetically supported for psoriasis.", gene="TYK2",
                 disease="psoriasis", scope="genetic_association", claim_type="genetic_support")


def test_gather_support_above_threshold():
    support = gather_support(_genetic_claim(), _StubStore(0.93))
    assert len(support) == 1 and support[0].value == 0.93
    verdict, _ = compose([], support=support)
    assert verdict is Verdict.SUPPORTED


def test_gather_support_below_threshold_is_empty():
    assert gather_support(_genetic_claim(), _StubStore(0.3)) == []
    verdict, _ = compose([], support=[])
    assert verdict is Verdict.INSUFFICIENT


def test_non_genetic_claim_gets_no_support():
    sel = Claim(text="MED12 is a selective regulator.", gene="MED12",
                scope="selective", claim_type="selectivity")
    assert gather_support(sel, _StubStore(0.99)) == []
