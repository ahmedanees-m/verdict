"""Select the checks relevant to a claim and decompose composite claims.

The confound library is fixed and every check is cheap, so the deterministic layer
runs all of them; the selector is where Claude states which checks are decisive for
this claim and why, and splits a composite claim into its separate assertions. That
reasoning is logged to the trace and shown in the dossier, so the judgment is legible
without giving the model any influence over the numbers.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..checks.base import Claim
from . import client
from .trace import Trace

CHECK_LIBRARY = {
    "direction": "does knockdown move the program the wrong way (a directional contradiction)",
    "essentiality": "is the gene broadly essential/pleiotropic, so a selectivity read is unsafe",
    "selectivity_safety": "is an organism-wide safety claim being drawn from cell-type-restricted data",
    "circularity": "does the cited evidence share provenance with the validating atlas",
    "range_scope": "does the claim reach beyond the range or scope the data can speak to",
    "power": "is the perturbation adequately powered (cross-guide concordance, significant genes)",
}

_SCHEMA = {
    "type": "object",
    "properties": {
        "relevant_checks": {
            "type": "array",
            "items": {"type": "string", "enum": list(CHECK_LIBRARY)},
            "description": "the checks whose outcome is decisive for this claim",
        },
        "rationale": {"type": "string",
                      "description": "one or two sentences on why those checks are the decisive ones"},
        "subclaims": {
            "type": "array",
            "items": {"type": "string"},
            "description": "if the claim bundles more than one assertion, the separate assertions; "
                           "otherwise an empty list",
        },
    },
    "required": ["relevant_checks", "rationale", "subclaims"],
    "additionalProperties": False,
}

_SYSTEM = (
    "You are the check selector for a target-validation engine with a fixed library of "
    "confound checks. Given a structured claim, name the checks whose result is decisive "
    "for it, in one short rationale, and if the claim bundles more than one assertion "
    "(for example, both that a target is safe and that its action is cell-type restricted) "
    "split it into its separate assertions. Do not state any measured value; you are "
    "choosing which checks matter, not computing them.\n\nThe library:\n"
    + "\n".join(f"- {k}: {v}" for k, v in CHECK_LIBRARY.items())
)


@dataclass
class Selection:
    relevant_checks: list[str] = field(default_factory=list)
    rationale: str = ""
    subclaims: list[str] = field(default_factory=list)


def select(claim: Claim, trace: Trace | None = None) -> Selection:
    data = client.extract(
        _SYSTEM,
        f"Claim text: {claim.text!r}\n"
        f"Parsed: gene={claim.gene}, program={claim.program}, scope={claim.scope}, "
        f"direction={claim.direction}, type={claim.claim_type}, "
        f"asserts_safety={claim.asserts_safety}, cited_source={claim.cited_source}",
        _SCHEMA,
    )
    sel = Selection(
        relevant_checks=[c for c in data.get("relevant_checks", []) if c in CHECK_LIBRARY],
        rationale=data.get("rationale", ""),
        subclaims=list(data.get("subclaims", [])),
    )
    if trace is not None:
        trace.log("select", f"decisive={sel.relevant_checks}: {sel.rationale}")
        if sel.subclaims:
            trace.log("decompose", "; ".join(sel.subclaims))
    return sel
