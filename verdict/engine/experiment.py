"""Propose the single most discriminating next experiment.

Given the verdict and which confound fired, Claude proposes one experiment that
would resolve the ambiguity the checks surfaced -- for an essentiality-driven
overclaim, an experiment that separates a viability effect from genuine program
regulation; for an out-of-scope safety claim, the assay that would actually speak to
organism-wide safety. This is heuristic guidance and is labelled as such; it states
no measured values, so it introduces no number to the output.
"""
from __future__ import annotations

from ..checks.base import CheckResult
from ..compose.composer import Verdict
from ..validator import validate_output
from . import client
from .trace import Trace

_SYSTEM = (
    "You are the experiment designer for a target-validation engine. Given a verdict and "
    "the confound the checks surfaced, propose the single most discriminating next "
    "experiment that would resolve it: the one that best separates the confound from the "
    "claimed effect. Two or three sentences, concrete about the perturbation, readout, and "
    "the comparison that settles it. State no numeric measurements."
)


def design(claim, results: list[CheckResult], verdict: Verdict,
           trace: Trace | None = None) -> str:
    fired = [r.check_name for r in results if r.status.value == "FIRED"]
    prompt = (
        f"Claim: {claim.text!r}\n"
        f"Verdict: {verdict.value}\n"
        f"Confound(s) that fired: {fired or 'none'}\n"
        f"Gene: {claim.gene}, program: {claim.program}, cell type: {claim.cell_type}"
    )
    text = client.reason(_SYSTEM, prompt, effort="low", max_tokens=1500)
    # No number should appear, but validate non-strict as a guard and drop any stray figure.
    stray = validate_output(text, [], strict=False)
    if trace is not None:
        note = "proposed" + (f" (dropped stray figures {stray})" if stray else "")
        trace.log("experiment", note)
    return text
