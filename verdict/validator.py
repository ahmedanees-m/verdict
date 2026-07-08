"""The enforcement point for the language layer.

Typing stops your CODE from emitting a bare number. This stops the LLM from
inventing a number in prose: every quantitative token in the model's output must
map to a receipt, or it is flagged.

A quantity is a standalone number. A digit that is part of an identifier -- CD4,
Th17, IL17A, the variant P1104A, the rsID rs34536443, a quarter label like 26Q1 --
is nomenclature, not a measurement, and is not treated as a quantity. Four-digit
years (1900-2099) are a structural allowlist, so a source can be dated without a
receipt; measured values in this domain (effect sizes, dependency scores, fractions)
never fall in that range.
"""
from __future__ import annotations
import re
from typing import Iterable
from .receipts import Gated

# A standalone number: not adjacent to a letter or another digit/decimal, and not the
# digit half of an identifier joined by a hyphen or slash (IL-4, CDK8/19). The captured
# group is the numeric core, with an optional ordinal suffix stripped for float parsing.
_NUM = re.compile(
    r"(?<![A-Za-z0-9.])(?<![A-Za-z0-9][-+/])"
    r"([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)(?:st|nd|rd|th)?(?![A-Za-z0-9])"
)


class FabricationError(Exception):
    """Raised when the LLM output contains a number with no backing receipt."""


def _fmt(v: float) -> str:
    s = f"{float(v):.6f}"
    return re.sub(r"\.?0+$", "", s)


def _is_year(token: str) -> bool:
    """A bare four-digit year in [1900, 2099] is structural, not a measurement."""
    if "." in token or "e" in token.lower() or token[:1] in "+-":
        return False
    return len(token) == 4 and token.isdigit() and 1900 <= int(token) <= 2099


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
    unbacked = [n for n in numbers_in(text)
                if _fmt(float(n)) not in allowed and not _is_year(n)]
    if strict and unbacked:
        raise FabricationError(f"LLM output contains un-receipted numbers: {unbacked}")
    return unbacked
