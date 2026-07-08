# Changelog

All notable changes to this project are documented in this file. The format
follows Keep a Changelog.

## [Unreleased]

## [0.1.0] - 2026-07-08

### Added
- Provenance-gated store: every value is returned with an HMAC-signed receipt naming its source dataset, file, computation, and query. A missing value is distinct from zero and yields an INSUFFICIENT result.
- Output validation that rejects any number not backed by a receipt.
- Ingestion for five functional-genomics sources: Zhu 2025 CD4+ T-cell Perturb-seq, Moonen 2026 variant-to-CRE-to-gene, DepMap 26Q1 Chronos gene effect, Open Targets Platform, and the Human Protein Atlas.
- Six deterministic confound checks: direction, essentiality, selectivity-safety, circularity, range-scope, and power.
- Verdict composer producing SUPPORTED, OVERCLAIMED, REFUTED, and INSUFFICIENT.
- Documented, versioned program marker gene sets.
- Pre-registered evaluation set with an expected verdict and firing check per case, and threshold calibration derived from the data distributions.
- Container image and a test suite of 32 tests, including the fabrication-impossible test.

[Unreleased]: https://github.com/ahmedanees-m/verdict/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ahmedanees-m/verdict/releases/tag/v0.1.0
