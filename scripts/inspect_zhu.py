"""Inspect the Zhu 2025 DE object before flattening.

Confirms the on-disk structure (obs columns, var index, layer names and density)
against the documented schema, and prints a TYK2 spot-check. Run once, read the
output, then finalize the flattener.
"""
from __future__ import annotations
import sys
import h5py
import numpy as np
import anndata as ad

PATH = sys.argv[1] if len(sys.argv) > 1 else "data/raw/marson/GWCD4i.DE_stats.h5ad"


def main() -> None:
    with h5py.File(PATH, "r") as f:
        print("=== top-level keys ===")
        print(list(f.keys()))
        print("\n=== layers ===")
        if "layers" in f:
            for k in f["layers"]:
                node = f["layers"][k]
                kind = "group(sparse)" if isinstance(node, h5py.Group) else f"dense{node.shape} {node.dtype}"
                print(f"  {k}: {kind}")
        print("\n=== varm ===")
        if "varm" in f:
            for k in f["varm"]:
                print(f"  {k}: {f['varm'][k]}")

    adata = ad.read_h5ad(PATH, backed="r")
    print("\n=== shape ===", adata.shape)
    print("\n=== obs columns ===")
    print(list(adata.obs.columns))
    print("\n=== obs dtypes ===")
    print(adata.obs.dtypes)
    print("\n=== obs head ===")
    print(adata.obs.head(3).to_string())
    print("\n=== var columns ===", list(adata.var.columns))
    print("=== var index name ===", adata.var.index.name)
    print("=== var head ===")
    print(adata.var.head(3).to_string())

    print("\n=== culture_condition values ===")
    cc_col = "culture_condition"
    print(adata.obs[cc_col].value_counts())

    print("\n=== TYK2 spot-check ===")
    name_col = "target_contrast_gene_name"
    mask = adata.obs[name_col].astype(str) == "TYK2"
    cols = [c for c in [
        "culture_condition", "target_contrast", "n_cells_target",
        "ontarget_effect_size", "ontarget_significant", "n_downstream",
        "n_total_de_genes", "guide_correlation_signif", "guide_correlation_all",
    ] if c in adata.obs.columns]
    print(adata.obs.loc[mask, cols].to_string())

    print("\n=== program-gene presence in var (IL17A, IFNG, IL23A, TBX21, RORC) ===")
    var_names = set(adata.var.index.astype(str))
    gene_name_col = "gene_name" if "gene_name" in adata.var.columns else None
    var_symbols = set(adata.var[gene_name_col].astype(str)) if gene_name_col else set()
    for g in ["IL17A", "IFNG", "IL23A", "TBX21", "RORC", "IL2", "TYK2"]:
        print(f"  {g}: in_index={g in var_names} in_gene_name={g in var_symbols}")

    print("\n=== one dense layer slice for TYK2 (Stim8hr) on 5 marker genes ===")
    if mask.any():
        obs_idx = np.where(mask.values & (adata.obs[cc_col].astype(str) == "Stim8hr").values)[0]
        if len(obs_idx):
            i = int(obs_idx[0])
            markers = [g for g in ["IFNG", "IL2", "TBX21"] if gene_name_col and g in var_symbols]
            if markers:
                jj = [int(np.where(adata.var[gene_name_col].astype(str) == g)[0][0]) for g in markers]
                lfc = adata.layers["log_fc"][i, jj]
                fdr = adata.layers["adj_p_value"][i, jj]
                z = adata.layers["zscore"][i, jj]
                for g, a, b, c in zip(markers, lfc, fdr, z):
                    print(f"  {g}: log_fc={a:.4f} adj_p={b:.4g} z={c:.4f}")


if __name__ == "__main__":
    main()
