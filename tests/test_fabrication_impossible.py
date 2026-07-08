"""FLAGSHIP: proves fabrication is structurally impossible. This is a demo asset."""
import pytest
from verdict.receipts import NO_RECEIPT
from verdict.gate import gate, verify, ProvenanceError
from verdict.validator import validate_output, FabricationError
from tests.helpers import gated


def test_missing_value_is_no_receipt_not_a_number():
    assert bool(NO_RECEIPT) is False          # falsy -- cannot be mistaken for 0.0
    assert gate(NO_RECEIPT) is NO_RECEIPT       # missing stays missing -> INSUFFICIENT downstream


def test_raw_float_cannot_cross_the_gate():
    with pytest.raises(ProvenanceError):
        gate(0.42)                              # a bare number is rejected at the boundary


def test_tampered_receipt_fails_verification():
    g = gated(1.23)
    g.receipt.value = 9.99                      # tamper after signing
    assert verify(g.receipt) is False
    with pytest.raises(ProvenanceError):
        gate(g)


def test_validator_catches_invented_number_in_prose():
    g = gated(1.23)
    assert validate_output("The effect size is 1.23 per the atlas.", [g], strict=False) == []
    with pytest.raises(FabricationError):
        validate_output("Effect size 1.23, FDR 0.007.", [g], strict=True)  # 0.007 unbacked
