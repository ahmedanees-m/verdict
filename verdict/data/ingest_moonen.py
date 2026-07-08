"""Parse the Moonen 2026 prioritized CRE-gene list into the trace store.

Source: supplementary Table S3 (``media-4.xlsx``, sheet ``prioritised_gene_list``),
which links a disease-associated variant (SNP) through a cis-regulatory element
(peak) to a target gene, with the prioritization source. This is the
variant-to-CRE-to-gene trace used as genetic support for a SUPPORTED verdict and
for the network view.

Run inside the project container::

    docker run --rm -v "$HOME/verdict:/app" verdict:latest \\
        python -m verdict.data.ingest_moonen
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SOURCE_DATASET = "Moonen2026"
SOURCE_FILE = "media-4.xlsx (Table S3: Prioritized CRE-gene list)"
SHEET = "prioritised_gene_list"

COLUMNS = {
    "peak": "cre",
    "SNP": "variant",
    "chr": "chr",
    "SNP_pos": "variant_pos",
    "SNP_trait": "disease",
    "gene_name": "gene_symbol",
    "gene_id": "gene_id",
    "prioritization_source": "source",
}


def ingest(xlsx_path: str = "data/raw/moonen/media-4.xlsx",
           out_dir: str = "data/store/moonen") -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    print(f"reading {xlsx_path} [{SHEET}]", flush=True)
    df = pd.read_excel(xlsx_path, sheet_name=SHEET)
    present = {src: dst for src, dst in COLUMNS.items() if src in df.columns}
    table = df[list(present)].rename(columns=present)
    # The source spreadsheet has mixed-type columns: chromosome mixes numeric
    # autosomes with X/Y, and Excel has coerced some gene symbols (MARCH1, SEPT7)
    # to dates. Store all trace fields as text so links stay usable.
    for col in table.columns:
        table[col] = table[col].astype(str)
    table.to_parquet(out / "cre_gene.parquet", index=False)
    print(f"wrote cre_gene.parquet ({len(table):,} links)", flush=True)

    diseases = sorted(table["disease"].dropna().astype(str).unique()) if "disease" in table else []
    tyk2 = table[table.get("gene_symbol", pd.Series(dtype=str)).astype(str) == "TYK2"]
    print(f"diseases: {diseases}", flush=True)
    print(f"TYK2 links: {len(tyk2)}", flush=True)
    if not tyk2.empty:
        print(tyk2.head(8).to_string(index=False), flush=True)

    manifest = {
        "source_dataset": SOURCE_DATASET, "source_file": SOURCE_FILE,
        "links": int(len(table)), "diseases": diseases,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("wrote manifest.json", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse the Moonen prioritized CRE-gene list.")
    ap.add_argument("--xlsx", default="data/raw/moonen/media-4.xlsx")
    ap.add_argument("--out", default="data/store/moonen")
    args = ap.parse_args()
    ingest(args.xlsx, args.out)


if __name__ == "__main__":
    main()
