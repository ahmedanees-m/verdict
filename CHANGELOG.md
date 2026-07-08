# Changelog

All notable changes to this project are documented in this file. The format
follows Keep a Changelog.

## [Unreleased]

### Added
- Reasoning layer: a claim parser, a check selector with logged rationale and composite-claim decomposition, an adjudicator, and a next-experiment designer, each recorded on an inspectable trace.
- Adversarial baseline and a number-contrast harness that put the same claim to the same model with and without the provenance gate and report which quantities in each answer carry a receipt.
- Genetic-support leg for the composer, so a SUPPORTED verdict on a genetic-association claim is computed from the Open Targets genetic-association score above a fixed threshold rather than retrieved.
- Document the pre-registered catch-selection gate and the faithfulness controls in the README.
- Provenance verification for the Moonen trace and program-marker coverage.

### Changed
- The output validator distinguishes a quantity from identifier nomenclature (gene, program, variant, and quarter labels) and allows four-digit years as a structural exception, so the fabrication gate does not flag names that contain digits.
- The adjudicator narrative is checked against the receipt ledger and restated if it introduces an unbacked number, with a ledger-only fallback that cannot contain one.
- The power check reports as not applicable for a genetic-association claim, which rests on no perturbation.
- Record program-marker coverage (measured of requested) in the effect receipts.
- Record the multi-gene assignment of Moonen candidate CRE-gene links, so the noncoding target-gene call is not overstated.
- Rest the TYK2 genetic-support case on the Open Targets score and the coding protective variant, and treat the Moonen link as candidate locus context.
- Lead the essentiality catch with a Mediator subunit (MED12) and keep CHD4 as a real-publication secondary framed at the evidence level.
- Report the cross-guide calibration explicitly as the significant-gene statistic.

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
