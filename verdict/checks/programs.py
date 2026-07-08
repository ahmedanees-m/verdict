"""Marker gene sets for transcriptional programs referenced by claims.

The direction check aggregates a perturbation's effect over the gene set that
defines a program, so the set determines the result. The sets are declared here,
explicitly and versioned, rather than inferred at run time: a check is only valid
if it fires on the store's numbers over a documented gene set, not on private
knowledge. A claim may also carry its own ``program_genes``, which take priority.

Sets are canonical effector markers drawn from standard immunology references.
Only genes present in the measured transcriptome contribute to an aggregate; the
rest are ignored and reported in the matched count.
"""
from __future__ import annotations

PROGRAMS_VERSION = "2026-07"

PROGRAMS: dict[str, dict] = {
    "Th17": {
        "description": "IL-23/IL-17 (Th17) effector program",
        "genes": ["IL17A", "IL17F", "IL23R", "RORC", "RORA", "CCR6",
                  "IL22", "IL26", "CCL20", "BATF", "AHR", "IL21", "STAT3"],
    },
    "Th1": {
        "description": "Th1 / interferon-gamma effector program",
        "genes": ["IFNG", "TBX21", "STAT1", "STAT4", "CXCL9", "CXCL10",
                  "IL12RB2", "IL18R1", "CCL5"],
    },
    "Th2": {
        "description": "Th2 effector program",
        "genes": ["IL4", "IL5", "IL13", "GATA3", "IL4R", "CCR4", "IL1RL1"],
    },
    "Treg": {
        "description": "regulatory T-cell program",
        "genes": ["FOXP3", "IL2RA", "CTLA4", "IKZF2", "TNFRSF18", "IL10"],
    },
    "activation": {
        "description": "T-cell activation / IL-2 program",
        "genes": ["IL2", "IL2RA", "CD69", "MYC", "TNFRSF9", "IRF4", "NR4A1"],
    },
}

# Free-text program phrasings mapped to a canonical key.
ALIASES: dict[str, str] = {
    "il-23/il-17 axis": "Th17",
    "il-23 / il-17 axis": "Th17",
    "il-17 axis": "Th17",
    "il-23/il-17": "Th17",
    "th17 program": "Th17",
    "th17": "Th17",
    "il-17": "Th17",
    "th1": "Th1",
    "interferon-gamma": "Th1",
    "type i/ii ifn": "Th1",
    "th2": "Th2",
    "treg": "Treg",
    "regulatory t cell": "Treg",
    "activation": "activation",
    "il-2": "activation",
}


def program_key(program: str | None) -> str | None:
    if not program:
        return None
    p = program.strip()
    if p in PROGRAMS:
        return p
    return ALIASES.get(p.lower())


def program_genes(program: str | None) -> list[str]:
    key = program_key(program)
    return list(PROGRAMS[key]["genes"]) if key else []


def resolve_program_genes(claim) -> list[str]:
    """Explicit ``claim.program_genes`` take priority; otherwise resolve the name."""
    if getattr(claim, "program_genes", None):
        return list(claim.program_genes)
    return program_genes(getattr(claim, "program", None))
