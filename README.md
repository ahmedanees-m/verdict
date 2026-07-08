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

## Faithfulness and the pre-registered gate

The direction check recomputes known immunology from the atlas as a control:
knockdown of a lineage-master regulator lowers its program (GATA3 lowers Th2,
TBX21 lowers Th1, STAT3 and AHR lower Th17), and knockdown of the T-cell-receptor
module collapses the activation and regulatory programs. Recovering textbook
biology from raw recomputation is what makes the catches trustworthy.

The primary catch was chosen through a pre-registered gate. The evaluation fixed
the direction-contradiction case as the intended primary, with essentiality as the
fallback if no clean, context-matched, well-powered contradiction existed in the
data. Scanning the three conditions found none (the strongest opposite-direction
effects are pleiotropic transcriptional machinery or scientifically contested), so
the pre-registered fallback selected essentiality as the primary catch. The gate
is documented, not reverse-fitted.

## Reasoning layer and the baseline contrast

The reasoning layer under `verdict/engine/` runs the actor and tool split end to
end. Claude parses the claim into the structured form, states which checks are
decisive and splits a composite claim into its parts, narrates the composed verdict,
and proposes the discriminating next experiment. The deterministic layer runs the
checks, gathers the genetic-support leg, and composes the verdict. Every decision is
recorded on an inspectable trace.

The adjudicator is given a ledger of the receipted values it may quote and nothing
else. Its narrative is passed through the output validator: a number with no backing
receipt is rejected and the narrative is restated, so the explanation is fluent while a
figure without provenance cannot reach the reader.

The number contrast puts the same claim to the same model twice, once unconstrained
and once through the engine, and reports which quantities in each answer carry a
receipt. The unconstrained answer states specific figures with no way to attach
provenance to any of them; the engine states a number only when it can name the file
and computation behind it. The contrast is over provenance, not correctness.
`scripts/demo_contrast.py` runs it.

## Status

Implemented: the provenance and refusal machinery, ingestion for the five data
sources, the six confound checks, the verdict composer with the genetic-support leg,
the reasoning layer, the adversarial baseline and number contrast, and the dossier
renderer. In progress: the application and the full evaluation write-up.

See [CHANGELOG.md](CHANGELOG.md) for release notes.

## License

MIT. See [LICENSE](LICENSE).
