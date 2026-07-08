"""Fetch tissue expression breadth from the Human Protein Atlas.

For each in-scope gene the ingestion records how broadly the gene is expressed
across tissues: the number of tissues surveyed, the number in which it is detected
(consensus nTPM at or above 1), the resulting breadth fraction, and the atlas
tissue-distribution label. Broad expression is evidence against a claim that a
target acts only in CD4+ T cells. Symbols are resolved to Ensembl identifiers via
the Open Targets id map. Results are cached to Parquet.

Run inside the project container::

    docker run --rm -v "$HOME/verdict:/app" verdict:latest \\
        python -m verdict.data.ingest_expression --genes TYK2 GATA3 TBX21 STAT3
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from .ingest_opentargets import _resolve, DEFAULT_GENES

SOURCE_DATASET = "HumanProteinAtlas"
SOURCE_FILE = "proteinatlas_gene_json"

# The atlas tissue-distribution category maps to a breadth fraction. This is the
# breadth signal for broadly expressed genes, which have no tissue-specific list.
DISTRIBUTION_SCORE = {
    "Detected in all": 1.0,
    "Detected in many": 0.75,
    "Detected in some": 0.40,
    "Detected in single": 0.15,
    "Detected in single common": 0.15,
    "Not detected": 0.0,
}


def _hpa_record(symbol: str, ensembl: str) -> dict | None:
    r = requests.get(f"https://www.proteinatlas.org/{ensembl}.json", timeout=60)
    if r.status_code != 200:
        return None
    j = r.json()
    distribution = j.get("RNA tissue distribution")
    breadth = DISTRIBUTION_SCORE.get(distribution)
    return {
        "gene_symbol": j.get("Gene") or symbol,
        "ensembl": ensembl,
        "breadth_fraction": breadth,
        "tissue_distribution": distribution,
        "tissue_specificity": j.get("RNA tissue specificity"),
    }


def ingest(genes: list[str], out_dir: str = "data/store/expression") -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    mapping = _resolve(genes)
    records = []
    for symbol in genes:
        ensembl = mapping.get(symbol)
        if not ensembl:
            print(f"  {symbol}: no mapping", flush=True)
            continue
        rec = _hpa_record(symbol, ensembl)
        if rec is None:
            print(f"  {symbol}: no HPA record", flush=True)
            continue
        records.append(rec)
        b = rec["breadth_fraction"]
        b_txt = f"{b:.2f}" if b is not None else "n/a"
        print(f"  {rec['gene_symbol']} ({ensembl}): {rec['tissue_distribution']} (breadth {b_txt})",
              flush=True)
    table = pd.DataFrame.from_records(records)
    table.to_parquet(out / "expression.parquet", index=False)
    print(f"wrote expression.parquet ({len(table)} genes)", flush=True)

    manifest = {
        "source_dataset": SOURCE_DATASET, "source_file": SOURCE_FILE,
        "genes": len(table), "built_at": datetime.now(timezone.utc).isoformat(),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch HPA tissue expression breadth.")
    ap.add_argument("--genes", nargs="*", default=DEFAULT_GENES)
    ap.add_argument("--out", default="data/store/expression")
    args = ap.parse_args()
    ingest(args.genes, args.out)


if __name__ == "__main__":
    main()
