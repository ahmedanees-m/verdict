"""The provenance-gated data store.

Every access returns a ``Gated`` value (or ``NO_RECEIPT``); the store never
returns a bare number. Query methods read the Parquet artifacts produced by the
``verdict.data.ingest_*`` modules through an in-memory DuckDB connection. When a
required artifact or value is absent the store returns ``NO_RECEIPT`` so the
caller degrades to INSUFFICIENT rather than substituting a value.
"""
from __future__ import annotations

from pathlib import Path
from typing import Union

import duckdb

from .receipts import Receipt, Gated, NO_RECEIPT, _NoReceipt
from .gate import sign

ZHU_DATASET = "Zhu2025"
ZHU_FILE = "GWCD4i.DE_stats.h5ad"
DEPMAP_DATASET = "DepMap_26Q1"
DEPMAP_FILE = "gene_effect.csv"
OT_DATASET = "OpenTargets"
OT_FILE = "platform_graphql_v4"
HPA_DATASET = "HumanProteinAtlas"
HPA_FILE = "proteinatlas_gene_json"
MOONEN_DATASET = "Moonen2026"
MOONEN_FILE = "media-4.xlsx (Table S3: Prioritized CRE-gene list)"

# Summary columns exposed per perturbation-condition, with the computation text
# recorded on each receipt.
_ZHU_SUMMARY = {
    "guide_correlation_signif": "cross-guide Pearson r of per-gene DE z-scores on significant genes",
    "guide_correlation_all": "cross-guide Pearson r of per-gene DE z-scores over all genes",
    "n_cells_target": "number of cells carrying a targeting guide for the perturbed gene",
    "ontarget_effect_size": "effect size of the perturbation on its intended target gene",
    "ontarget_significant": "on-target knockdown significant at 10% FDR",
    "n_downstream": "count of significant trans-effects (excluding the on-target effect)",
    "n_downstream_pct": "within-condition percentile of n_downstream across all perturbations",
}


class Store:
    """DuckDB-backed provenance store over the ingested Parquet artifacts."""

    def __init__(self, base_dir: str = "data/store"):
        self.base = Path(base_dir)
        self.con = duckdb.connect(database=":memory:")
        self._zhu = False
        self._depmap = False
        self._opentargets = False
        self._expression = False
        self._load_zhu()
        self._load_depmap()
        self._load_table("opentargets", "opentargets/opentargets.parquet")
        self._load_table("expression", "expression/expression.parquet")
        self._load_table("moonen", "moonen/cre_gene.parquet")

    # ---- setup ----
    def _load_zhu(self) -> None:
        zdir = self.base / "zhu"
        pert, gene, de = zdir / "perturbation.parquet", zdir / "gene.parquet", zdir / "de.parquet"
        if not (pert.exists() and gene.exists() and de.exists()):
            return
        self.con.execute(f"CREATE TABLE zhu_pert AS SELECT * FROM read_parquet('{pert.as_posix()}')")
        self.con.execute(f"CREATE TABLE zhu_gene AS SELECT * FROM read_parquet('{gene.as_posix()}')")
        self.con.execute(f"CREATE VIEW zhu_de AS SELECT * FROM read_parquet('{de.as_posix()}')")
        self._zhu = True

    def _load_depmap(self) -> None:
        path = self.base / "depmap" / "gene_effect.parquet"
        if not path.exists():
            return
        self.con.execute(
            f"CREATE TABLE depmap AS SELECT * FROM read_parquet('{path.as_posix()}')")
        self._depmap = True

    def _load_table(self, name: str, relpath: str) -> None:
        setattr(self, f"_{name}", False)
        path = self.base / relpath
        if not path.exists():
            return
        self.con.execute(f"CREATE TABLE {name} AS SELECT * FROM read_parquet('{path.as_posix()}')")
        setattr(self, f"_{name}", True)

    # ---- receipt helper ----
    def _receipt(self, value, *, dataset, file, computation, query) -> Union[Gated, _NoReceipt]:
        if value is None:
            return NO_RECEIPT
        r = sign(Receipt(value=value, source_dataset=dataset, source_file=file,
                         computation=computation, query=query))
        return Gated(value=value, receipt=r)

    # ---- resolvers ----
    def _pert_code(self, gene: str, condition: str):
        row = self.con.execute(
            "SELECT pert_code FROM zhu_pert "
            "WHERE (perturbation = ? OR perturbation_id = ?) AND condition = ? LIMIT 1",
            [gene, gene, condition],
        ).fetchone()
        return None if row is None else int(row[0])

    def _gene_codes(self, genes) -> list[tuple[int, str]]:
        genes = [g for g in (genes or []) if g]
        if not genes:
            return []
        ph = ",".join("?" * len(genes))
        rows = self.con.execute(
            f"SELECT gene_code, gene_symbol FROM zhu_gene "
            f"WHERE gene_symbol IN ({ph}) OR gene_ensembl IN ({ph})",
            list(genes) + list(genes),
        ).fetchall()
        return [(int(c), str(s)) for c, s in rows]

    # ---- Zhu queries ----
    def zhu_effect(self, gene: str, program_genes, condition: str):
        """Aggregate effect of ``gene`` knockdown over a program gene set.

        Returns a dict of receipted values (``mean_log_fc``, ``mean_zscore``,
        ``n_genes``, ``n_significant``) or ``NO_RECEIPT`` when the perturbation or
        gene set is not present. ``mean_log_fc`` carries the direction signal:
        its sign is the mean transcriptional response of the program to knockdown.
        """
        if not self._zhu:
            return NO_RECEIPT
        pc = self._pert_code(gene, condition)
        codes = self._gene_codes(program_genes)
        if pc is None or not codes:
            return NO_RECEIPT
        code_list = [c for c, _ in codes]
        ph = ",".join("?" * len(code_list))
        row = self.con.execute(
            f"SELECT avg(log_fc), avg(zscore), count(*), "
            f"       sum(CASE WHEN adj_p_value < 0.10 THEN 1 ELSE 0 END) "
            f"FROM zhu_de WHERE pert_code = ? AND gene_code IN ({ph})",
            [pc] + code_list,
        ).fetchone()
        mean_lfc, mean_z, n, n_sig = row
        if not n or mean_lfc is None:
            return NO_RECEIPT
        q = f"pert_code={pc}, gene_code in [{len(code_list)} program genes], condition={condition}"
        n_sig = int(n_sig or 0)
        return {
            "mean_log_fc": self._receipt(
                round(float(mean_lfc), 6), dataset=ZHU_DATASET, file=ZHU_FILE,
                computation=(f"mean signed log2 fold change of {gene} knockdown over {int(n)} "
                             f"program genes ({n_sig} significant at FDR<0.10), {condition}"),
                query=q),
            "mean_zscore": self._receipt(
                round(float(mean_z), 6), dataset=ZHU_DATASET, file=ZHU_FILE,
                computation=f"mean DE z-score of {gene} knockdown over {int(n)} program genes, {condition}",
                query=q),
            "n_genes": self._receipt(
                int(n), dataset=ZHU_DATASET, file=ZHU_FILE,
                computation=f"program genes matched in the measured transcriptome, {condition}",
                query=q),
            "n_significant": self._receipt(
                n_sig, dataset=ZHU_DATASET, file=ZHU_FILE,
                computation=f"program genes significant at FDR<0.10 under {gene} knockdown, {condition}",
                query=q),
        }

    def zhu_gene_effects(self, gene: str, program_genes, condition: str) -> list[Gated]:
        """Per-gene receipted effects for the program gene set (evidence detail)."""
        if not self._zhu:
            return []
        pc = self._pert_code(gene, condition)
        codes = self._gene_codes(program_genes)
        if pc is None or not codes:
            return []
        by_code = {c: s for c, s in codes}
        ph = ",".join("?" * len(by_code))
        rows = self.con.execute(
            f"SELECT gene_code, log_fc, adj_p_value, zscore "
            f"FROM zhu_de WHERE pert_code = ? AND gene_code IN ({ph})",
            [pc] + list(by_code),
        ).fetchall()
        out = []
        for gene_code, log_fc, adj_p, z in rows:
            sym = by_code.get(int(gene_code), str(gene_code))
            g = self._receipt(
                round(float(log_fc), 6),
                dataset=ZHU_DATASET, file=ZHU_FILE,
                computation=f"log2 fold change of {sym} on {gene} knockdown, {condition} (FDR={float(adj_p):.3g})",
                query=f"pert_code={pc}, gene_code={int(gene_code)} ({sym}), condition={condition}",
            )
            if g is not NO_RECEIPT:
                out.append(g)
        return out

    def zhu_summary(self, gene: str, condition: str):
        """All per-perturbation summary statistics as a dict of receipted values."""
        if not self._zhu:
            return NO_RECEIPT
        cols = [c for c in _ZHU_SUMMARY if self._has_column("zhu_pert", c)]
        if not cols:
            return NO_RECEIPT
        row = self.con.execute(
            f"SELECT {', '.join(cols)} FROM zhu_pert "
            f"WHERE (perturbation = ? OR perturbation_id = ?) AND condition = ? LIMIT 1",
            [gene, gene, condition],
        ).fetchone()
        if row is None:
            return NO_RECEIPT
        out: dict[str, Gated] = {}
        for col, value in zip(cols, row):
            if value is None:
                continue
            v = int(value) if isinstance(value, bool) else value
            g = self._receipt(
                v, dataset=ZHU_DATASET, file=ZHU_FILE,
                computation=f"{_ZHU_SUMMARY[col]} for {gene} in {condition}",
                query=f"zhu_pert[{gene}, {condition}].{col}",
            )
            if g is not NO_RECEIPT:
                out[col] = g
        return out or NO_RECEIPT

    def zhu_power(self, gene: str, condition: str):
        s = self.zhu_summary(gene, condition)
        if s is NO_RECEIPT:
            return NO_RECEIPT
        return s.get("guide_correlation_signif", NO_RECEIPT)

    def zhu_breadth(self, gene: str, condition: str):
        s = self.zhu_summary(gene, condition)
        if s is NO_RECEIPT:
            return NO_RECEIPT
        return s.get("n_downstream_pct", NO_RECEIPT)

    def _has_column(self, table: str, column: str) -> bool:
        rows = self.con.execute(f"PRAGMA table_info('{table}')").fetchall()
        return any(r[1] == column for r in rows)

    # ---- DepMap essentiality ----
    def depmap_essentiality(self, gene: str):
        """Per-gene DepMap Chronos summary as a dict of receipted values."""
        if not self._depmap:
            return NO_RECEIPT
        row = self.con.execute(
            "SELECT chronos_mean, chronos_median, frac_dependent, is_common_essential, n_lines "
            "FROM depmap WHERE gene_symbol = ? LIMIT 1",
            [gene],
        ).fetchone()
        if row is None:
            return NO_RECEIPT
        chronos_mean, chronos_median, frac_dependent, common, n_lines = row
        q = f"depmap[{gene}] over {int(n_lines)} cell lines"
        out = {
            "chronos_median": self._receipt(
                round(float(chronos_median), 4), dataset=DEPMAP_DATASET, file=DEPMAP_FILE,
                computation=f"median Chronos gene effect of {gene} across {int(n_lines)} cell lines",
                query=q),
            "chronos_mean": self._receipt(
                round(float(chronos_mean), 4), dataset=DEPMAP_DATASET, file=DEPMAP_FILE,
                computation=f"mean Chronos gene effect of {gene} across {int(n_lines)} cell lines",
                query=q),
            "frac_dependent": self._receipt(
                round(float(frac_dependent), 4), dataset=DEPMAP_DATASET, file=DEPMAP_FILE,
                computation=f"fraction of cell lines dependent on {gene} (Chronos < -0.5)",
                query=q),
            "common_essential": self._receipt(
                int(bool(common)), dataset=DEPMAP_DATASET, file=DEPMAP_FILE,
                computation=f"{gene} dependent in >=90% of cell lines (common-essential)",
                query=q),
        }
        return out

    # ---- Open Targets ----
    def opentargets(self, gene: str):
        if not self._opentargets:
            return NO_RECEIPT
        row = self.con.execute(
            "SELECT genetic_association_score, n_safety_liabilities, tractability_approved_drug, efo "
            "FROM opentargets WHERE gene_symbol = ? LIMIT 1",
            [gene],
        ).fetchone()
        if row is None:
            return NO_RECEIPT
        genetic, n_safety, approved, efo = row
        out: dict[str, Gated] = {}
        if genetic is not None:
            g = self._receipt(round(float(genetic), 4), dataset=OT_DATASET, file=OT_FILE,
                              computation=f"genetic-association score of {gene} with {efo}",
                              query=f"opentargets[{gene}, {efo}].genetic_association")
            if g is not NO_RECEIPT:
                out["genetic_association_score"] = g
        out["safety_liabilities"] = self._receipt(
            int(n_safety), dataset=OT_DATASET, file=OT_FILE,
            computation=f"count of Open Targets safety liabilities for {gene}",
            query=f"opentargets[{gene}].safetyLiabilities")
        out["tractability_approved_drug"] = self._receipt(
            int(bool(approved)), dataset=OT_DATASET, file=OT_FILE,
            computation=f"{gene} has an approved small-molecule drug (tractability)",
            query=f"opentargets[{gene}].tractability")
        return out or NO_RECEIPT

    # ---- expression breadth (Human Protein Atlas) ----
    def expression_breadth(self, gene: str):
        if not self._expression:
            return NO_RECEIPT
        row = self.con.execute(
            "SELECT breadth_fraction, tissue_distribution FROM expression "
            "WHERE gene_symbol = ? LIMIT 1",
            [gene],
        ).fetchone()
        if row is None or row[0] is None:
            return NO_RECEIPT
        breadth, distribution = row
        return self._receipt(
            round(float(breadth), 4), dataset=HPA_DATASET, file=HPA_FILE,
            computation=f"tissue expression breadth of {gene} (HPA RNA tissue distribution: "
                        f"{distribution})",
            query=f"expression[{gene}].breadth_fraction")

    # ---- Moonen variant-to-CRE-to-gene trace ----
    def moonen_links(self, gene: str, disease: str | None = None) -> list[dict]:
        if not self._moonen:
            return []
        sql = "SELECT cre, variant, chr, variant_pos, disease, gene_symbol, source FROM moonen WHERE gene_symbol = ?"
        params: list = [gene]
        if disease:
            sql += " AND lower(disease) LIKE ?"
            params.append(f"%{disease.lower()}%")
        cols = [c[0] for c in self.con.execute(sql, params).description]
        return [dict(zip(cols, row)) for row in self.con.execute(sql, params).fetchall()]

    def moonen_trace(self, gene: str, disease: str | None = None):
        """Receipted count of variant-to-CRE-to-gene links for a gene and disease."""
        links = self.moonen_links(gene, disease)
        if not links:
            return NO_RECEIPT
        variants = sorted({str(l["variant"]) for l in links if l.get("variant")})
        cres = sorted({str(l["cre"]) for l in links if l.get("cre")})
        scope = f" for {disease}" if disease else ""
        return self._receipt(
            len(links), dataset=MOONEN_DATASET, file=MOONEN_FILE,
            computation=f"variant-to-CRE-to-gene links resolving to {gene}{scope}: "
                        f"{len(variants)} variants through {len(cres)} cis-regulatory elements",
            query=f"moonen[gene={gene}{', disease=' + disease if disease else ''}]")
