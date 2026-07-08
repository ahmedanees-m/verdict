"""Flatten the Zhu 2025 CD4+ T-cell Perturb-seq DE object into the store.

Source: ``GWCD4i.DE_stats.h5ad`` (Marson lab, s3://genome-scale-tcell-perturb-seq).
The object holds, for each (perturbed gene, culture condition) pair, per-gene
differential-expression statistics in dense ``.layers`` (log_fc, adj_p_value,
zscore) over the measured transcriptome, plus per-perturbation summary columns
in ``.obs``.

Ingestion produces three Parquet artifacts under ``data/store/zhu``:

* ``perturbation.parquet`` - one row per (perturbation, condition) with the
  power and breadth summary statistics, plus a within-condition breadth
  percentile computed here.
* ``gene.parquet`` - the measured-gene dimension (symbol and Ensembl id).
* ``de.parquet`` - the long per-gene effect table keyed by integer codes.

Run inside the project container, e.g.::

    docker run --rm -v "$HOME/verdict:/app" verdict:latest \\
        python -m verdict.data.ingest_zhu --limit 2000   # quick check
    docker run --rm -v "$HOME/verdict:/app" verdict:latest \\
        python -m verdict.data.ingest_zhu                 # full run
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import anndata as ad
import h5py
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

SOURCE_DATASET = "Zhu2025"
SOURCE_FILE = "GWCD4i.DE_stats.h5ad"
CONDITIONS = ("Rest", "Stim8hr", "Stim48hr")
DE_LAYERS = ("log_fc", "adj_p_value", "zscore")

# Column names as documented in the atlas data_sharing_readme. Resolved against
# the real object at run time, with fallbacks, so a rename does not break ingest.
OBS_NAME = "target_contrast_gene_name"
OBS_ENSEMBL = "target_contrast"
OBS_CONDITION = "culture_condition"
OBS_SUMMARY = (
    "n_cells_target",
    "ontarget_effect_size",
    "ontarget_significant",
    "n_downstream",
    "n_total_de_genes",
    "guide_correlation_signif",
    "guide_correlation_all",
    "neighboring_gene_KD",
    "distal_offtarget_flag",
    "low_target_gex",
    "single_guide_estimate",
)


def _resolve(columns, *candidates):
    for c in candidates:
        if c in columns:
            return c
    return None


def _gene_dimension(adata) -> pd.DataFrame:
    var = adata.var
    symbol = _resolve(var.columns, "gene_name")
    ensembl = _resolve(var.columns, "gene_ids", "gene_id")
    symbols = var[symbol].astype(str).to_numpy() if symbol else var.index.astype(str).to_numpy()
    ensembls = var[ensembl].astype(str).to_numpy() if ensembl else var.index.astype(str).to_numpy()
    return pd.DataFrame(
        {
            "gene_code": np.arange(var.shape[0], dtype=np.int32),
            "gene_symbol": symbols,
            "gene_ensembl": ensembls,
        }
    )


def _perturbation_table(adata) -> pd.DataFrame:
    obs = adata.obs.reset_index(drop=True)
    cols = obs.columns
    out = pd.DataFrame({"pert_code": np.arange(obs.shape[0], dtype=np.int32)})
    out["perturbation"] = obs[_resolve(cols, OBS_NAME)].astype(str).to_numpy()
    ens = _resolve(cols, OBS_ENSEMBL)
    out["perturbation_id"] = obs[ens].astype(str).to_numpy() if ens else ""
    out["condition"] = obs[_resolve(cols, OBS_CONDITION)].astype(str).to_numpy()
    for c in OBS_SUMMARY:
        name = _resolve(cols, c)
        if name is not None:
            out[c] = obs[name].to_numpy()
    # Within-condition percentile of trans-effect breadth (n_downstream), used by
    # the essentiality/pleiotropy check. Higher percentile == broader effect.
    if "n_downstream" in out.columns:
        out["n_downstream_pct"] = (
            out.groupby("condition")["n_downstream"].rank(pct=True).to_numpy()
        )
    return out


def _flatten_layers(h5ad_path: str, n_obs: int, n_var: int, out_path: Path,
                    block: int, limit: int | None) -> int:
    if limit is not None:
        n_obs = min(n_obs, limit)
    gene_codes = np.arange(n_var, dtype=np.int32)
    schema = pa.schema(
        [
            ("pert_code", pa.int32()),
            ("gene_code", pa.int32()),
            ("log_fc", pa.float32()),
            ("adj_p_value", pa.float32()),
            ("zscore", pa.float32()),
        ]
    )
    written = 0
    writer = pq.ParquetWriter(out_path, schema, compression="zstd")
    try:
        with h5py.File(h5ad_path, "r") as f:
            dsets = {name: f["layers"][name] for name in DE_LAYERS}
            for start in range(0, n_obs, block):
                stop = min(start + block, n_obs)
                rows = stop - start
                layers = {name: np.asarray(dsets[name][start:stop, :], dtype=np.float32)
                          for name in DE_LAYERS}
                pert_codes = np.repeat(np.arange(start, stop, dtype=np.int32), n_var)
                batch = pa.record_batch(
                    {
                        "pert_code": pert_codes,
                        "gene_code": np.tile(gene_codes, rows),
                        "log_fc": layers["log_fc"].reshape(-1),
                        "adj_p_value": layers["adj_p_value"].reshape(-1),
                        "zscore": layers["zscore"].reshape(-1),
                    },
                    schema=schema,
                )
                writer.write_batch(batch)
                written += rows * n_var
                print(f"  flattened obs {stop}/{n_obs} ({written:,} rows)", flush=True)
    finally:
        writer.close()
    return written


def ingest(
    h5ad_path: str = "data/raw/marson/GWCD4i.DE_stats.h5ad",
    out_dir: str = "data/store/zhu",
    block: int = 1000,
    limit: int | None = None,
) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    print(f"reading {h5ad_path} (backed)", flush=True)
    adata = ad.read_h5ad(h5ad_path, backed="r")
    print(f"shape: {adata.shape}", flush=True)

    genes = _gene_dimension(adata)
    genes.to_parquet(out / "gene.parquet", index=False)
    print(f"wrote gene.parquet ({len(genes):,} genes)", flush=True)

    perturbation = _perturbation_table(adata)
    perturbation.to_parquet(out / "perturbation.parquet", index=False)
    print(f"wrote perturbation.parquet ({len(perturbation):,} perturbations)", flush=True)

    n_obs, n_var = adata.shape
    n_rows = _flatten_layers(h5ad_path, n_obs, n_var, out / "de.parquet", block=block, limit=limit)
    print(f"wrote de.parquet ({n_rows:,} rows)", flush=True)

    manifest = {
        "source_dataset": SOURCE_DATASET,
        "source_file": SOURCE_FILE,
        "shape": list(adata.shape),
        "conditions": list(CONDITIONS),
        "de_layers": list(DE_LAYERS),
        "de_rows": n_rows,
        "limit": limit,
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("wrote manifest.json", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Flatten the Zhu DE object into the store.")
    ap.add_argument("--h5ad", default="data/raw/marson/GWCD4i.DE_stats.h5ad")
    ap.add_argument("--out", default="data/store/zhu")
    ap.add_argument("--block", type=int, default=1000)
    ap.add_argument("--limit", type=int, default=None, help="flatten only the first N perturbations")
    args = ap.parse_args()
    ingest(args.h5ad, args.out, block=args.block, limit=args.limit)


if __name__ == "__main__":
    main()
