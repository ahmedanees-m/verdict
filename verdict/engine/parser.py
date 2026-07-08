"""Claim parser -- Claude turns NL into a structured Claim (strict JSON schema).

Implement with the Anthropic Messages API using a current Claude model. The system
prompt must constrain Claude to: (a) emit only the schema; (b) never invent a value;
(c) narrate ONLY over receipts downstream. Log the parse to the Trace.
"""
from __future__ import annotations
from ..checks.base import Claim
from .trace import Trace


def parse(text: str, trace: Trace | None = None) -> Claim:
    """TODO(Step 5): call Claude -> structured fields. Stub returns a shell Claim."""
    if trace:
        trace.log("parse", f"(stub) parsed claim text; wire to Claude in Step 5")
    return Claim(text=text)
