"""The reasoning layer: Claude decides what a claim means, which checks apply, how to
narrate the verdict, and what experiment resolves it. The deterministic layer computes
every number. See pipeline.evaluate for the end-to-end flow and contrast.contrast for
the side-by-side against an unconstrained baseline."""
from __future__ import annotations

from .pipeline import EngineResult, evaluate
from .contrast import ContrastReport, annotate, contrast
from .trace import Trace

__all__ = ["evaluate", "EngineResult", "contrast", "ContrastReport", "annotate", "Trace"]
