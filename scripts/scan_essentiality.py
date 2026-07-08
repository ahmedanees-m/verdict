"""Surface essentiality-primary candidates and demonstrate the check.

Lists genes that are both broadly essential (DepMap) and top-breadth (Zhu), the
population where a 'selective regulator' claim is confounded by essentiality, and
runs the check on the strongest candidate plus TYK2 as a non-essential control.
"""
from __future__ import annotations

from verdict.store import Store
from verdict.checks.base import Claim
from verdict.checks import essentiality

CANDIDATES = """
SELECT p.perturbation, p.n_downstream, p.n_downstream_pct,
       d.chronos_median, d.frac_dependent, d.is_common_essential
FROM zhu_pert p JOIN depmap d ON p.perturbation = d.gene_symbol
WHERE p.condition = ? AND p.n_downstream_pct >= 0.97
  AND (d.is_common_essential OR d.chronos_median < -0.5)
ORDER BY p.n_downstream DESC
LIMIT 30
"""


def main() -> None:
    store = Store()
    if not (store._zhu and store._depmap):
        raise SystemExit(f"stores not built (zhu={store._zhu} depmap={store._depmap})")

    condition = "Stim8hr"
    rows = store.con.execute(CANDIDATES, [condition]).fetchdf()
    print(f"=== essential + top-breadth candidates ({condition}) ===")
    print(rows.to_string(index=False))

    demo = [rows.iloc[0]["perturbation"], "GATA3", "TYK2"]
    print("\n=== essentiality check demonstration ===")
    for gene in demo:
        claim = Claim(
            text=f"{gene} selectively regulates a CD4+ T-cell program",
            gene=gene, program="Th17", scope="selective",
            cell_type="CD4+ T", condition=condition)
        result = essentiality.run(claim, store)
        print(f"\n{gene}: {result.status.value}")
        print(f"  {result.rationale}")


if __name__ == "__main__":
    main()
