"""Render a Functional Target-Validation Dossier. Every number shown carries a receipt.
The Claude narrative and the deterministic line-items sit side by side; the scope
caveat is mandatory."""
from __future__ import annotations
from ..checks.base import CheckResult
from .composer import Verdict

SCOPE_CAVEAT = ("Verdict scoped to CD4+ T-cell functional genomics. A REFUTED/OVERCLAIMED "
                "verdict means 'not supported given this data', never 'the target is wrong'.")


def render(claim, results: list[CheckResult], verdict: Verdict, rationale: str,
           next_experiment: str = "", narrative: str = "", selection: str = "") -> str:
    lines = [f"# Target-Validation Dossier", f"**Claim:** {claim.text}", ""]
    lines.append(f"**Verdict:** {verdict.value}. {rationale}")
    if narrative:
        lines.append("")
        lines.append(narrative)
    if selection:
        lines.append("")
        lines.append(f"_Checks selected:_ {selection}")
    lines.append("")
    lines.append("## Confound line-items")
    for r in results:
        nums = ", ".join(
            f"{g.value} [{g.receipt.source_dataset}:{g.receipt.computation}]" for g in r.evidence
        ) or "(no receipted numbers)"
        lines.append(f"- **{r.check_name}** ({r.status.value}): {r.rationale}  \n  {nums}")
    if next_experiment:
        lines.append(f"\n## Next experiment (heuristic)\n{next_experiment}")
    lines.append(f"\n---\n_{SCOPE_CAVEAT}_")
    return "\n".join(lines)
