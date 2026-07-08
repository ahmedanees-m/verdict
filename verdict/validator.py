"""The enforcement point for the language layer.

Typing stops your CODE from emitting a bare number. This stops the LLM from
inventing a number in prose: every numeric token in the model's output must map
to a receipt, or it is flagged.

NOTE (v0): matching is normalized-string based. Harden with tolerance matching
and a structural-integer allowlist (years, counts) before production.
"""
from __future__ import annotations
import re
from typing import Iterable
from .receipts import Gated

_NUM = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


class FabricationError(Exception):
    """Raised when the LLM output contains a number with no backing receipt."""


def _fmt(v: float) -> str:
    s = f"{float(v):.6f}"
    return re.sub(r"\.?0+$", "", s)


def numbers_in(text: str) -> list[str]:
    return _NUM.findall(text)


def _receipted(receipts: Iterable[Gated]) -> set[str]:
    out = set()
    for g in receipts:
        if isinstance(g.value, (int, float)):
            out.add(_fmt(g.value))
    return out


def validate_output(text: str, receipts: Iterable[Gated], *, strict: bool = True) -> list[str]:
    """Return numbers in `text` not backed by a receipt. In strict mode, raise if any."""
    allowed = _receipted(receipts)
    unbacked = [n for n in numbers_in(text) if _fmt(float(n)) not in allowed]
    if strict and unbacked:
        raise FabricationError(f"LLM output contains un-receipted numbers: {unbacked}")
    return unbacked
