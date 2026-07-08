"""Gene-ID harmonization -- the silent killer. Map every source to ONE canonical
ID (Ensembl recommended) via pybiomart or a static table. Log unmapped genes."""
from __future__ import annotations


def to_ensembl(symbol_or_id: str) -> str | None:
    raise NotImplementedError("Implement canonical gene mapping in Step 1.")
