"""The provenance gate: the single choke point every number crosses.

Raw floats cannot pass. Only a `Gated` value with a valid HMAC, or `NO_RECEIPT`.
This is 'refuses to fabricate', implemented -- not promised in a prompt.
"""
from __future__ import annotations
import hmac
import hashlib
import os
from typing import Union
from .receipts import Receipt, Gated, NO_RECEIPT, _NoReceipt


class ProvenanceError(Exception):
    """Raised when an un-receipted or tampered value reaches the boundary."""


def _key() -> bytes:
    k = os.environ.get("VERDICT_HMAC_KEY")
    if not k:
        raise ProvenanceError(
            "VERDICT_HMAC_KEY is not set; refusing to run ungated. "
            "Set it in the environment (never commit it)."
        )
    return k.encode()


def sign(receipt: Receipt) -> Receipt:
    receipt.hmac = hmac.new(_key(), receipt.canonical_bytes(), hashlib.sha256).hexdigest()
    return receipt


def verify(receipt: Receipt) -> bool:
    if receipt.hmac is None:
        return False
    expected = hmac.new(_key(), receipt.canonical_bytes(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, receipt.hmac)


def gate(x: Union[Gated, _NoReceipt]):
    """Anything reaching compose/LLM passes through here."""
    if x is NO_RECEIPT:
        return NO_RECEIPT
    if not isinstance(x, Gated):
        raise ProvenanceError(
            f"Ungated value reached the boundary: {type(x)!r}. Every number must carry a receipt."
        )
    if not verify(x.receipt):
        raise ProvenanceError("Receipt failed HMAC verification (tampered or unsigned).")
    return x
