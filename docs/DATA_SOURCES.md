# Data sources

Each value returned by the store carries a receipt naming its source dataset,
file, and computation. The datasets are listed here with their versions and
access paths.

## Zhu 2025 CD4+ T-cell Perturb-seq

- Reference: bioRxiv 10.64898/2025.12.23.696273.
- File: `GWCD4i.DE_stats.h5ad`, the genome-scale differential-expression object
  (33,983 perturbation-condition pairs, 10,282 measured genes, dense per-gene
  log fold change, adjusted p-value, and z-score layers for Rest, Stim8hr, and
  Stim48hr).
- Access: public S3 bucket `genome-scale-tcell-perturb-seq/marson2025_data`
  (unsigned). The 120 to 173 GB per-donor cell-level objects are not used.
- Use: functional effect on a program gene set, trans-effect breadth, and the
  cross-guide concordance and cell-count power statistics.

## Moonen 2026 variant to CRE to gene

- Reference: bioRxiv 10.64898/2026.03.09.710372.
- File: supplementary Table S3 (`media-4.xlsx`, sheet `prioritised_gene_list`),
  linking a disease-associated variant through a cis-regulatory element to a
  target gene with the prioritization source.
- Use: the genetic-support trace for a SUPPORTED verdict and the network view.

## DepMap Chronos gene effect

- Version: 26Q1.
- File: `gene_effect.csv`, the Chronos gene-effect matrix (1,208 cell lines,
  18,531 genes). More negative means more essential.
- Use: per-gene essentiality (mean and median effect, dependent fraction, and a
  common-essential flag defined as dependent in at least 90 percent of lines).

## Open Targets Platform

- Access: GraphQL API v4 (`api.platform.opentargets.org`), queried per gene.
- Use: tractability, the count of safety liabilities, and the genetic-association
  component of the target-disease association score.

## Human Protein Atlas

- Access: per-gene JSON (`proteinatlas.org`).
- Use: tissue expression breadth, from the RNA tissue-distribution category, as
  evidence on whether a target is broadly expressed.

## Gene identifiers

Genes are matched by symbol across sources, with Ensembl identifiers recorded
where available. TYK2 (ENSG00000105397) is used as a cross-source reference.
