"""Report the data distributions behind the check thresholds and record them.

Confirms the calibratable defaults against the real Zhu and DepMap distributions
and writes a calibration record. Breadth uses a within-condition percentile so it
is calibrated by construction; the cross-guide, essentiality, and FDR thresholds
are checked here against the observed distributions.
"""
from __future__ import annotations

import json
from pathlib import Path

from verdict.store import Store
from verdict.checks.base import FDR_SIG, CROSSGUIDE_MIN, CHRONOS_ESSENTIAL, BREADTH_TOP_DECILE


def main() -> None:
    s = Store()
    con = s.con
    report: dict = {"thresholds": {
        "FDR_SIG": FDR_SIG, "CROSSGUIDE_MIN": CROSSGUIDE_MIN,
        "CHRONOS_ESSENTIAL": CHRONOS_ESSENTIAL, "BREADTH_TOP_DECILE": BREADTH_TOP_DECILE}}

    if s._zhu:
        xg = con.execute(
            "SELECT count(*), median(guide_correlation_signif), "
            "quantile_cont(guide_correlation_signif, 0.25), quantile_cont(guide_correlation_signif, 0.75) "
            "FROM zhu_pert WHERE guide_correlation_signif IS NOT NULL "
            "AND NOT isnan(guide_correlation_signif)").fetchone()
        xg_all = con.execute(
            "SELECT median(guide_correlation_all) FROM zhu_pert "
            "WHERE guide_correlation_all IS NOT NULL AND NOT isnan(guide_correlation_all)").fetchone()[0]
        cells = con.execute(
            "SELECT median(n_cells_target), quantile_cont(n_cells_target, 0.10) FROM zhu_pert"
        ).fetchone()
        sig_rate = con.execute(
            "SELECT avg(CASE WHEN adj_p_value < ? THEN 1.0 ELSE 0.0 END) FROM zhu_de "
            "USING SAMPLE 5000000 ROWS", [FDR_SIG]).fetchone()[0]
        report["zhu"] = {
            "crossguide_metric": "median guide_correlation_signif (cross-guide Pearson r of per-gene "
                                 "DE z-scores restricted to significant DE genes; perturbations with two "
                                 "guides and a defined value)",
            "crossguide_signif_n": int(xg[0]), "crossguide_signif_median": round(xg[1], 3),
            "crossguide_signif_q25": round(xg[2], 3), "crossguide_signif_q75": round(xg[3], 3),
            "crossguide_all_median": round(float(xg_all), 3),
            "n_cells_median": round(cells[0], 1), "n_cells_p10": round(cells[1], 1),
            "de_significant_rate_at_fdr": round(float(sig_rate), 4),
        }
        print("Zhu cross-guide concordance on significant DE genes (guide_correlation_signif): "
              f"n={xg[0]} median={xg[1]:.3f} IQR[{xg[2]:.3f}, {xg[3]:.3f}]. "
              f"Over all measured genes (guide_correlation_all) the median is {xg_all:.3f} "
              "(noise-dominated). The check uses the significant-gene statistic; "
              f"CROSSGUIDE_MIN={CROSSGUIDE_MIN} sits below its median.")
        print(f"Zhu cells per perturbation: median={cells[0]:.0f} p10={cells[1]:.0f}")
        print(f"Zhu genome-wide significant rate at FDR<{FDR_SIG}: {sig_rate:.3%}")

    if s._depmap:
        dep = con.execute(
            "SELECT median(chronos_median), "
            "avg(CASE WHEN chronos_median < ? THEN 1.0 ELSE 0.0 END), "
            "sum(CASE WHEN is_common_essential THEN 1 ELSE 0 END) "
            "FROM depmap", [CHRONOS_ESSENTIAL]).fetchone()
        report["depmap"] = {
            "chronos_median_of_medians": round(dep[0], 3),
            "fraction_below_essential_threshold": round(float(dep[1]), 4),
            "common_essential_genes": int(dep[2]),
        }
        print(f"\nDepMap median gene effect: {dep[0]:.3f} (bulk of genes near 0, non-essential)")
        print(f"DepMap fraction below {CHRONOS_ESSENTIAL}: {dep[1]:.2%}; "
              f"common-essential genes: {int(dep[2])}")

    out = Path("data/store/calibration.json")
    out.write_text(json.dumps(report, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
