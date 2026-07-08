"""Inspectable reasoning trace -- every Claude decision is logged and shown in the UI.
Legible judgment is what earns the Claude Use score."""
from __future__ import annotations
from dataclasses import dataclass, field
import time


@dataclass
class TraceEntry:
    step: str          # "parse" | "decompose" | "select" | "adjudicate" | "experiment"
    detail: str
    at: float = field(default_factory=time.time)


class Trace:
    def __init__(self):
        self.entries: list[TraceEntry] = []

    def log(self, step: str, detail: str) -> None:
        self.entries.append(TraceEntry(step, detail))

    def as_markdown(self) -> str:
        return "\n".join(f"- **{e.step}**: {e.detail}" for e in self.entries)
