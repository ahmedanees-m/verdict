"""Circularity -- the claim's cited evidence shares a source with the validating atlas."""
from __future__ import annotations
from .base import Claim, CheckResult, Status
from ..manifest import screen_of

name = "circularity"

# which atlas is used to validate (the functional recomputation source)
VALIDATING_ATLAS = "Zhu2025"


def run(claim: Claim, store) -> CheckResult:
    """Fire iff claim.cited_source's screen == the validating atlas's screen.
    Implemented on plain manifest data (no query needed) -- but requires built_from
    to be populated for real, else the check is theatre.
    """
    if not claim.cited_source:
        return CheckResult(name, Status.INSUFFICIENT,
                           "No cited source on the claim; cannot assess circularity.")
    cited_screen = screen_of(claim.cited_source)
    atlas_screen = screen_of(VALIDATING_ATLAS)
    if cited_screen is None:
        return CheckResult(name, Status.INSUFFICIENT,
                           f"Unknown provenance for cited source {claim.cited_source!r}.")
    if cited_screen == atlas_screen:
        return CheckResult(name, Status.FIRED,
                           f"Circular: cited evidence and the validating atlas both derive "
                           f"from {atlas_screen!r}.")
    return CheckResult(name, Status.NOT_FIRED,
                       "Cited evidence and validating atlas have distinct provenance.")
