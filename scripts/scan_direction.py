"""Scan the Zhu store for direction-hero candidates.

For each program, rank perturbations by the strength of their aggregate effect on
the program gene set, keeping only those with significant on-target knockdown.
Reports the strongest raising and lowering perturbations with their power
statistics. A knockdown that significantly raises a program is a candidate to
contradict a published 'gene promotes program' claim; a knockdown that lowers it
contradicts a 'represses' claim. Cross-reference the candidates with the
literature to select the hero case.
"""
from __future__ import annotations

import argparse

from verdict.store import Store
from verdict.checks.programs import PROGRAMS, program_genes

QUERY = """
WITH prog AS (
    SELECT gene_code FROM zhu_gene WHERE gene_symbol IN ({placeholders})
),
agg AS (
    SELECT d.pert_code,
           avg(d.log_fc)  AS mean_lfc,
           avg(d.zscore)  AS mean_z,
           sum(CASE WHEN d.adj_p_value < 0.10 THEN 1 ELSE 0 END) AS n_sig,
           count(*)       AS n
    FROM zhu_de d JOIN prog USING (gene_code)
    GROUP BY d.pert_code
)
SELECT p.perturbation, a.mean_lfc, a.mean_z, a.n_sig, a.n,
       p.guide_correlation_signif AS xg_sig, p.guide_correlation_all AS xg_all,
       p.n_downstream_pct AS breadth_pct, p.n_cells_target AS n_cells
FROM agg a JOIN zhu_pert p USING (pert_code)
WHERE p.condition = ? AND p.ontarget_significant AND a.n_sig >= ?
ORDER BY a.mean_z {order}
LIMIT ?
"""


def scan(store: Store, program: str, condition: str, min_sig: int, top: int) -> None:
    genes = program_genes(program)
    codes = store._gene_codes(genes)
    measured = [s for _, s in codes]
    print(f"\n### {program} in {condition} "
          f"({len(measured)}/{len(genes)} genes measured: {sorted(measured)})")
    if not measured:
        print("  no measured genes; skipping")
        return
    ph = ",".join("?" * len(measured))
    for label, order in (("knockdown RAISES program (top +)", "DESC"),
                         ("knockdown LOWERS program (top -)", "ASC")):
        sql = QUERY.format(placeholders=ph, order=order)
        rows = store.con.execute(sql, measured + [condition, min_sig, top]).fetchall()
        print(f"  -- {label} --")
        print(f"     {'gene':12s} {'mean_lfc':>9s} {'mean_z':>8s} {'n_sig':>5s} "
              f"{'xg_sig':>7s} {'xg_all':>7s} {'breadth':>7s} {'n_cells':>7s}")
        for r in rows:
            gene, mean_lfc, mean_z, n_sig, n, xg_sig, xg_all, breadth, n_cells = r
            xs = f"{xg_sig:.2f}" if xg_sig is not None and xg_sig == xg_sig else "  nan"
            xa = f"{xg_all:.2f}" if xg_all is not None and xg_all == xg_all else "  nan"
            print(f"     {gene:12s} {mean_lfc:9.3f} {mean_z:8.2f} {int(n_sig):5d} "
                  f"{xs:>7s} {xa:>7s} {breadth:7.2f} {int(n_cells):7d}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", default="Stim8hr")
    ap.add_argument("--min-sig", type=int, default=3, help="min significant program genes")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--programs", nargs="*", default=list(PROGRAMS))
    args = ap.parse_args()

    store = Store()
    if not store._zhu:
        raise SystemExit("Zhu store not built")
    for program in args.programs:
        scan(store, program, args.condition, args.min_sig, args.top)


if __name__ == "__main__":
    main()
