"""Build a small, committed sample store keyed to the evaluation genes.

The full store is multi-gigabyte and lives off the repository. This subsets it to
the perturbations and rows the pre-registered evaluation touches, so that
`python scripts/run_eval.py` reproduces the verdict matrix from a clean clone. Every
value written here is an exact row-subset of the full store, so the receipts are
byte-for-byte the same; nothing is recomputed or approximated.

Run against the full store (`data/store`); writes `data/sample_store`.
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import yaml

SRC = Path("data/store")
DST = Path("data/sample_store")


def eval_genes() -> list[str]:
    cases = yaml.safe_load(open("EVAL_SET.yaml"))["cases"]
    genes = {(c.get("parsed") or {}).get("gene") for c in cases}
    return sorted(g for g in genes if g and g not in {"any", "all"})


def main() -> None:
    con = duckdb.connect()
    genes = eval_genes()
    for sub in ("zhu", "depmap", "opentargets", "expression", "moonen"):
        (DST / sub).mkdir(parents=True, exist_ok=True)

    pert_src = (SRC / "zhu/perturbation.parquet").as_posix()
    ph = ",".join("?" * len(genes))
    pcodes = [int(r[0]) for r in con.execute(
        f"SELECT pert_code FROM read_parquet('{pert_src}') WHERE perturbation IN ({ph})",
        genes).fetchall()]
    pc_list = ",".join(str(p) for p in pcodes)

    def copy(select_sql: str, dst_rel: str) -> None:
        con.execute(f"COPY ({select_sql}) TO '{(DST / dst_rel).as_posix()}' (FORMAT PARQUET)")

    # Zhu: the eval perturbations (all conditions), the whole gene map, and only the
    # eval perturbations' DE rows.
    copy(f"SELECT * FROM read_parquet('{pert_src}') WHERE pert_code IN ({pc_list})",
         "zhu/perturbation.parquet")
    copy(f"SELECT * FROM read_parquet('{(SRC / 'zhu/gene.parquet').as_posix()}')",
         "zhu/gene.parquet")
    copy(f"SELECT * FROM read_parquet('{(SRC / 'zhu/de.parquet').as_posix()}') "
         f"WHERE pert_code IN ({pc_list})", "zhu/de.parquet")

    # The reference tables are already small; carry them whole so the demo resolves
    # any gene's essentiality, expression, safety, and locus links.
    for rel in ("depmap/gene_effect.parquet", "opentargets/opentargets.parquet",
                "expression/expression.parquet", "moonen/cre_gene.parquet"):
        copy(f"SELECT * FROM read_parquet('{(SRC / rel).as_posix()}')", rel)

    print("genes:", genes)
    print("pert_codes:", pcodes)
    total = 0
    for p in sorted(DST.rglob("*.parquet")):
        size = p.stat().st_size
        total += size
        print(f"{p.as_posix():44s} {size:>10,} bytes")
    print(f"{'total':44s} {total:>10,} bytes")


if __name__ == "__main__":
    main()
