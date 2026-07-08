"""Parse a natural-language claim into a structured Claim.

Claude reads the sentence and fills the schema with the claim's assertions. It
never invents a measured value, score, or effect size: those come only from the
provenance-gated store, downstream. A field the claim does not state is left null.
The parse is recorded on the trace.
"""
from __future__ import annotations

from ..checks.base import Claim
from ..checks.programs import resolve_program_genes
from . import client
from .trace import Trace

_SCHEMA = {
    "type": "object",
    "properties": {
        "gene": {"type": ["string", "null"], "description": "target gene symbol, or null"},
        "variant": {"type": ["string", "null"], "description": "rsID or protein variant, or null"},
        "disease": {"type": ["string", "null"]},
        "program": {"type": ["string", "null"],
                    "description": "transcriptional program named or implied "
                                   "(Th1, Th2, Th17, Treg, activation), or null"},
        "direction": {"type": ["string", "null"],
                      "description": "promotes | represses | required_for | regulates | null"},
        "scope": {"type": ["string", "null"],
                  "description": "cell_type_specific | organism_wide | selective | "
                                 "genetic_association | null"},
        "cell_type": {"type": ["string", "null"]},
        "condition": {"type": ["string", "null"], "description": "Rest | Stim8hr | Stim48hr | null"},
        "cited_source": {"type": ["string", "null"],
                         "description": "dataset the claim cites as its evidence, or null"},
        "asserts_safety": {"type": "boolean",
                           "description": "true only if the claim asserts the target is safe"},
        "claim_type": {"type": "string",
                       "enum": ["selectivity", "safety", "genetic_support",
                                "directional", "composite"]},
    },
    "required": ["gene", "variant", "disease", "program", "direction", "scope",
                 "cell_type", "condition", "cited_source", "asserts_safety", "claim_type"],
    "additionalProperties": False,
}

# The store keys on canonical tokens; Claude may phrase them freely. Normalize the two
# fields the checks match on exactly, so "CD4+ T cells" resolves to the assay's CD4+ T.
_CONDITIONS = {"rest": "Rest", "resting": "Rest",
               "stim8hr": "Stim8hr", "stim8h": "Stim8hr", "8hr": "Stim8hr",
               "stim48hr": "Stim48hr", "stim48h": "Stim48hr", "48hr": "Stim48hr"}


def _canon_cell_type(ct: str | None) -> str | None:
    if not ct:
        return ct
    return "CD4+ T" if "cd4" in ct.lower() else ct


def _canon_condition(c: str | None) -> str | None:
    if not c:
        return None
    key = c.lower().replace(" ", "").replace("-", "").replace("_", "")
    return _CONDITIONS.get(key)  # unknown -> None, so the checks apply their default


_SYSTEM = (
    "You are the claim parser for a target-validation engine. Extract the structured "
    "assertions of a drug-target claim exactly as stated. Do not infer measured values, "
    "association scores, or effect sizes; extract only what the claim asserts, and leave "
    "a field null when the claim does not state it. Map a named or clearly implied program "
    "to its canonical key (Th1, Th2, Th17, Treg, activation). Set asserts_safety true only "
    "when the claim asserts the target is safe. Choose claim_type as the single best fit: "
    "selectivity (a specificity assertion), safety, genetic_support (a genetic-association "
    "claim), directional (promotes/represses a program), or composite (more than one of "
    "these at once)."
)


def parse(text: str, trace: Trace | None = None) -> Claim:
    data = client.extract(_SYSTEM, f"Claim: {text!r}", _SCHEMA)
    claim = Claim(
        text=text,
        gene=data.get("gene"), variant=data.get("variant"), disease=data.get("disease"),
        program=data.get("program"), direction=data.get("direction"), scope=data.get("scope"),
        cell_type=_canon_cell_type(data.get("cell_type")),
        condition=_canon_condition(data.get("condition")),
        cited_source=data.get("cited_source"),
        asserts_safety=bool(data.get("asserts_safety")),
        claim_type=data.get("claim_type"),
    )
    claim.program_genes = resolve_program_genes(claim) or None
    if trace is not None:
        trace.log(
            "parse",
            f"gene={claim.gene}, program={claim.program}, scope={claim.scope}, "
            f"direction={claim.direction}, type={claim.claim_type}, "
            f"asserts_safety={claim.asserts_safety}",
        )
    return claim
