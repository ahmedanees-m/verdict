# VERDICT

VERDICT is a provenance-gated target-validation engine. Given a drug-target
claim, it recomputes the answer from primary immune-disease functional-genomics
atlases, runs a library of deterministic checks for the confounds that make
target claims fail, and returns a verdict in which every reported number is
traceable to the file and computation that produced it. When a required value is
not available, it returns Insufficient rather than an unbacked number.

## Verdicts

| Verdict | Meaning |
|---|---|
| SUPPORTED | The claim is backed by a receipted evidence chain |
| OVERCLAIMED | The claim reaches beyond what the evidence supports (for example, selectivity confounded by essentiality, or safety asserted from cell-type-restricted data) |
| REFUTED | The data contradicts the claim, or the supporting evidence is circular |
| INSUFFICIENT | The claim cannot be evaluated from the available data |

All verdicts are scoped to CD4+ T-cell functional genomics. An OVERCLAIMED or
REFUTED verdict means "not supported given this data", not "the target is wrong".

## Architecture

VERDICT separates judgment from computation.

- A reasoning layer parses a claim into a structured form, selects which checks
  apply, and adjudicates ambiguous cases. Its decisions are logged to an
  inspectable trace.
- A deterministic layer performs every computation. A provenance-gated store
  returns each value with a receipt (source dataset, file, computation, and
  query) signed with a runtime key. Six confound checks read the store and return
  a status with receipted evidence. A composer maps the check states to a verdict.

A value never crosses into the reasoning layer or output as a bare number. Model
output is scanned so that any figure it reports must map to a receipt.

## Data sources

| Source | Use | Provenance |
|---|---|---|
| Zhu 2025 CD4+ T-cell Perturb-seq | Functional effect, effect breadth, direction | bioRxiv 10.64898/2025.12.23.696273 |
| Moonen 2026 variant to CRE to gene | Genetic support trace | bioRxiv 10.64898/2026.03.09.710372 |
| DepMap Chronos gene effect (26Q1) | Essentiality | depmap.org |
| Open Targets Platform | Tractability, safety, genetic association | platform.opentargets.org |
| Human Protein Atlas | Tissue expression breadth | proteinatlas.org |

## Installation

The project runs in a container.

```bash
docker build -t verdict:latest .
docker run --rm -e VERDICT_HMAC_KEY="$(python -c 'import secrets;print(secrets.token_hex(32))')" \
    verdict:latest pytest -q
```

For a local environment instead:

```bash
pip install -e ".[dev]"
export VERDICT_HMAC_KEY="$(python -c 'import secrets;print(secrets.token_hex(32))')"
pytest -q
```

## Data and evaluation

Ingestion scripts under `verdict/data/` build the store from the sources above;
`scripts/` contains the download, inspection, calibration, and evaluation
utilities. With the store built, the pre-registered evaluation runs with:

```bash
python scripts/run_eval.py
```

The evaluation set in `EVAL_SET.yaml` is fixed before the checks are wired to
data and records, for each claim, the expected verdict and the check expected to
fire. Thresholds are calibrated against the observed data distributions
(`scripts/calibrate.py`).

## Repository layout

```
verdict/
  receipts.py  gate.py  validator.py   provenance and refusal machinery
  store.py     data/                   the provenance-gated store and ingestion
  checks/                              the six confound checks
  compose/                             the verdict composer and dossier
  engine/                              the reasoning layer and baseline
  eval/                                the evaluation runner
scripts/                               download, inspection, calibration, evaluation
tests/                                 unit tests, including the fabrication-impossible test
```

## Status

Implemented: the provenance and refusal machinery, ingestion for the five data
sources, the six confound checks, and the verdict composer. In progress: the
composer genetic-support chain, the reasoning layer, the dossier renderer, and
the application.

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## License

MIT. See [LICENSE](LICENSE).
