"""Full evaluation of one claim: parse, select, check, compose, adjudicate, design.

This is the actor/tool split end to end. Claude parses the claim, states which
checks are decisive, narrates the verdict over receipts, and proposes the next
experiment. The deterministic layer runs the six confound checks, gathers the
positive genetic-support leg, and composes the verdict. Every decision is logged to
the trace, and every number in the output is receipted.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..checks.base import Claim, CheckResult
from ..checks.registry import CHECKS
from ..compose.composer import Verdict, compose
from ..compose.dossier import render
from ..compose.support import gather_support
from . import adjudicator, experiment, parser, selector
from .selector import Selection
from .trace import Trace


@dataclass
class EngineResult:
    claim: Claim
    selection: Selection
    results: list[CheckResult]
    support: list = field(default_factory=list)
    verdict: Verdict = Verdict.INSUFFICIENT
    rationale: str = ""
    narrative: str = ""
    next_experiment: str = ""
    trace: Trace = field(default_factory=Trace)
    receipts: list = field(default_factory=list)
    dossier_md: str = ""


def evaluate(text: str, store, trace: Trace | None = None) -> EngineResult:
    trace = trace or Trace()

    claim = parser.parse(text, trace)
    selection = selector.select(claim, trace)

    results = [run(claim, store) for run in CHECKS.values()]
    support = gather_support(claim, store)
    verdict, rationale = compose(results, support=support)
    trace.log("compose", f"{verdict.value} -- {rationale}")

    narrative = adjudicator.adjudicate(claim, results, verdict, rationale, support, trace)
    next_experiment = experiment.design(claim, results, verdict, trace)

    receipts = [g for r in results for g in r.evidence] + list(support)
    dossier_md = render(claim, results, verdict, rationale,
                        next_experiment=next_experiment, narrative=narrative,
                        selection=selection.rationale)

    return EngineResult(
        claim=claim, selection=selection, results=results, support=support,
        verdict=verdict, rationale=rationale, narrative=narrative,
        next_experiment=next_experiment, trace=trace, receipts=receipts,
        dossier_md=dossier_md,
    )
