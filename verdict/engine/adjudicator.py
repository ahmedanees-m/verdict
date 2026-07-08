"""Write the verdict narrative, citing only receipted numbers.

The verdict itself is decided by the deterministic composer, not here; the
adjudicator explains it. Claude is given a ledger of the receipted values it may
quote and nothing else. Its output is passed through the fabrication validator: a
number with no backing receipt is rejected. On rejection the adjudicator asks Claude
once to restate using only receipted values, and if that still fails it falls back to
a narrative assembled directly from the ledger, which cannot contain an unbacked
number. So the explanation is fluent, but a fabricated figure cannot reach the reader.
"""
from __future__ import annotations

from ..checks.base import CheckResult
from ..compose.composer import Verdict
from ..validator import FabricationError, _fmt, validate_output
from . import client
from .trace import Trace


def _lines(gated: list) -> str:
    out = []
    for g in gated:
        val = _fmt(g.value) if isinstance(g.value, (int, float)) else str(g.value)
        out.append(f"- {val}  ({g.receipt.computation}; source {g.receipt.source_dataset})")
    return "\n".join(out) if out else "(none)"


_SYSTEM = (
    "You are the adjudicator for a provenance-gated target-validation engine. Explain the "
    "verdict that the deterministic layer has already decided, in three to five sentences, "
    "for a scientific reader. Explain it on the basis the composer states: the decisive "
    "checks are the ones the composer names, and the positive genetic-support basis, when "
    "present, is what makes a SUPPORTED verdict. A check that fired but is not named by the "
    "composer (for example a perturbation-power note) is a secondary annotation, not the "
    "reason for the verdict; do not present it as the basis. Strict rule: you may state a "
    "numeric value only by copying it exactly from the receipted ledger you are given. Do not "
    "compute, round, estimate, or recall any other number, and do not write years or counts "
    "that are not in the ledger. Refer to genes, programs, variants, and cell types by name "
    "(these are identifiers, not measurements). Keep the scope honest: an OVERCLAIMED or "
    "REFUTED verdict means 'not supported given this CD4+ T-cell data', never that the target "
    "is wrong."
)


def _fallback(claim, results, verdict: Verdict, rationale: str, ledger_text: str) -> str:
    fired = [r for r in results if r.status.value == "FIRED"]
    parts = [f"Verdict {verdict.value}. {rationale}"]
    for r in fired:
        parts.append(r.rationale)
    if ledger_text and ledger_text != "(none)":
        parts.append("Receipted evidence:\n" + ledger_text)
    return " ".join(parts[:2]) + ("\n" + "\n".join(parts[2:]) if len(parts) > 2 else "")


def adjudicate(claim, results: list[CheckResult], verdict: Verdict, rationale: str,
               support: list | None = None, trace: Trace | None = None) -> str:
    support = support or []
    check_gated = [g for r in results for g in r.evidence]
    gated = check_gated + list(support)
    ledger_text = _lines(check_gated)
    support_text = _lines(support)
    prompt = (
        f"Claim: {claim.text!r}\n"
        f"Decided verdict: {verdict.value}\n"
        f"Composer rationale: {rationale}\n"
        f"Check outcomes:\n"
        + "\n".join(f"- {r.check_name}: {r.status.value} -- {r.rationale}" for r in results)
        + f"\n\nConfound-check receipted ledger (numbers you may cite):\n{ledger_text}"
        + f"\n\nGenetic-support basis (the positive evidence, when present):\n{support_text}"
    )
    narrative = ""
    for attempt in (1, 2):
        try:
            narrative = client.reason(_SYSTEM, prompt, effort="medium", max_tokens=4000)
            validate_output(narrative, gated, strict=True)
            if trace is not None:
                trace.log("adjudicate", f"narrative accepted (attempt {attempt}, "
                                        f"every number receipted)")
            return narrative
        except FabricationError as e:
            if trace is not None:
                trace.log("adjudicate", f"attempt {attempt} rejected by the fabrication gate: {e}")
            prompt += (f"\n\nYour previous answer was rejected: it contained numbers with no "
                       f"receipt ({e}). Restate using only values from the ledger above, or "
                       f"describe them qualitatively.")
    fallback = _fallback(claim, results, verdict, rationale, _lines(gated))
    if trace is not None:
        trace.log("adjudicate", "fell back to a ledger-only narrative (guaranteed receipted)")
    return fallback
