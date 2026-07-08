from verdict.gate import gate, verify
from tests.helpers import gated


def test_valid_gated_value_passes():
    g = gated(0.51)
    assert verify(g.receipt) is True
    assert gate(g) is g


def test_receipt_carries_provenance():
    g = gated(0.51)
    assert g.receipt.source_dataset == "Zhu2025"
    assert g.receipt.computation and g.receipt.query
