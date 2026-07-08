"""Summarise DepMap Chronos gene effect into a per-gene essentiality table.

Source: the DepMap 26Q1 Chronos ``gene_effect.csv`` (rows are cell lines, columns
are ``SYMBOL (ENTREZID)`` gene effect scores; more negative means more essential).
For each gene the ingestion records the mean and median effect across cell lines
and the fraction of lines in which the gene is dependent (effect below the
essentiality threshold). A gene dependent in at least ``COMMON_FRACTION`` of lines
is flagged common-essential, an operational reproduction of the DepMap panel-wide
essential definition computed directly from the released matrix.

Run inside the project container::

    docker run --rm -v "$HOME/verdict:/app" verdict:latest \\
        python -m verdict.data.ingest_depmap
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

SOURCE_DATASET = "DepMap_26Q1"
SOURCE_FILE = "gene_effect.csv"
DEPENDENT_THRESHOLD = -0.5   # Chronos effect below this counts as a dependency
COMMON_FRACTION = 0.90       # dependent in at least this fraction of lines => common-essential

_COLUMN = re.compile(r"^(?P<symbol>.+?)\s*\((?P<entrez>\d+)\)$")


def _parse_columns(columns) -> pd.DataFrame:
    rows = []
    for c in columns:
        m = _COLUMN.match(str(c))
        if m:
            rows.append((c, m.group("symbol"), int(m.group("entrez"))))
        else:
            rows.append((c, str(c), None))
    return pd.DataFrame(rows, columns=["column", "gene_symbol", "entrez"])


def ingest(csv_path: str = "data/raw/depmap/gene_effect.csv",
           out_dir: str = "data/store/depmap") -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    print(f"reading {csv_path}", flush=True)
    df = pd.read_csv(csv_path, index_col=0)
    n_lines = df.shape[0]
    print(f"cell lines={n_lines} genes={df.shape[1]}", flush=True)

    values = df.to_numpy(dtype=np.float32)
    finite = np.isfinite(values)
    dependent = finite & (values < DEPENDENT_THRESHOLD)
    n_finite = finite.sum(axis=0)
    with np.errstate(invalid="ignore"):
        chronos_mean = np.nanmean(np.where(finite, values, np.nan), axis=0)
        chronos_median = np.nanmedian(np.where(finite, values, np.nan), axis=0)
    frac_dependent = np.where(n_finite > 0, dependent.sum(axis=0) / np.maximum(n_finite, 1), np.nan)

    meta = _parse_columns(df.columns)
    table = meta.assign(
        chronos_mean=chronos_mean,
        chronos_median=chronos_median,
        frac_dependent=frac_dependent,
        n_lines=n_finite,
        is_common_essential=frac_dependent >= COMMON_FRACTION,
    )
    table = table.drop(columns=["column"])
    table.to_parquet(out / "gene_effect.parquet", index=False)
    print(f"wrote gene_effect.parquet ({len(table):,} genes)", flush=True)

    n_common = int(table["is_common_essential"].sum())
    print(f"common-essential genes: {n_common:,}", flush=True)
    for g in ("TYK2", "POLR2A", "RPL13", "MED12"):
        row = table[table["gene_symbol"] == g]
        if not row.empty:
            r = row.iloc[0]
            print(f"  {g}: median={r.chronos_median:.3f} frac_dependent={r.frac_dependent:.2f} "
                  f"common_essential={bool(r.is_common_essential)}", flush=True)

    manifest = {
        "source_dataset": SOURCE_DATASET,
        "source_file": SOURCE_FILE,
        "cell_lines": int(n_lines),
        "genes": int(len(table)),
        "dependent_threshold": DEPENDENT_THRESHOLD,
        "common_fraction": COMMON_FRACTION,
        "common_essential_genes": n_common,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("wrote manifest.json", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Summarise DepMap Chronos gene effect.")
    ap.add_argument("--csv", default="data/raw/depmap/gene_effect.csv")
    ap.add_argument("--out", default="data/store/depmap")
    args = ap.parse_args()
    ingest(args.csv, args.out)


if __name__ == "__main__":
    main()
