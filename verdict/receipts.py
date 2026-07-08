"""Receipts + gated values: the currency of the trust guarantee.

A number in VERDICT is never a bare float. It is a `Gated` value carrying a
`Receipt` that says exactly which dataset, file, and computation produced it.
A missing value is `NO_RECEIPT` (falsy) -- never silently 0.0.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Optional, Union
from pydantic import BaseModel, Field

Value = Union[float, int, str, None]


class Receipt(BaseModel):
    value: Value
    source_dataset: str            # "Zhu2025" | "Moonen2026" | "DepMap_25QX" | "OpenTargets_vNN" | "GTEx"
    source_file: str
    computation: str               # e.g. "mean signed effect over program-P gene set, Stim8hr"
    query: str                     # the exact filter/query used
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    hmac: Optional[str] = None     # set by gate.sign()

    def canonical_bytes(self) -> bytes:
        """Deterministic serialization for signing (excludes the hmac field itself)."""
        d = self.model_dump(exclude={"hmac"}, mode="json")
        return json.dumps(d, sort_keys=True, separators=(",", ":")).encode()


class Gated(BaseModel):
    """The ONLY type allowed to cross into compose/ or the LLM layer."""
    value: Value
    receipt: Receipt


class _NoReceipt:
    """Sentinel forcing INSUFFICIENT. A missing value is not a zero."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "NO_RECEIPT"

    def __bool__(self) -> bool:
        return False


NO_RECEIPT = _NoReceipt()
