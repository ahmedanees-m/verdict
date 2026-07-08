"""Anthropic client for the reasoning layer.

Centralizes model choice, adaptive thinking, structured output, and refusal
handling so every Claude call in the engine is consistent. The key is read from
the environment; it is never written to the repository.

The layer follows a strict actor/tool split. Claude decides *what* a claim means,
which checks apply, how to narrate a result, and what experiment resolves it. The
deterministic layer computes *every number*. A call here is always a judgment or a
structured extraction, never a computation, so no measured value originates in the
model.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

DEFAULT_MODEL = "claude-opus-4-8"


def model() -> str:
    """Resolve the model. Override with VERDICT_MODEL (e.g. a cheaper tier)."""
    return os.environ.get("VERDICT_MODEL", DEFAULT_MODEL)


def _supports_effort(m: str) -> bool:
    """Adaptive thinking and the effort control are available on Opus 4.6+,
    Sonnet 4.6/5, and Fable 5. Older or Haiku-tier models take neither."""
    m = m.lower()
    if "haiku" in m:
        return False
    return m not in {"claude-sonnet-4-5", "claude-opus-4-1", "claude-opus-4-0"}


@lru_cache(maxsize=1)
def _client():
    import anthropic  # imported lazily so the package loads without the SDK configured
    return anthropic.Anthropic()


def _text(resp) -> str:
    if getattr(resp, "stop_reason", None) == "refusal":
        raise RuntimeError("Claude declined the request (stop_reason=refusal).")
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def reason(system: str, user: str, *, effort: str = "medium", max_tokens: int = 6000) -> str:
    """A judgment call: adaptive thinking on where supported, plain text out."""
    m = model()
    kwargs = dict(
        model=m, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}],
    )
    if _supports_effort(m):
        kwargs["thinking"] = {"type": "adaptive"}
        kwargs["output_config"] = {"effort": effort}
    return _text(_client().messages.create(**kwargs))


def extract(system: str, user: str, schema: dict, *, max_tokens: int = 1200) -> dict:
    """An extraction call: output constrained to `schema`, no thinking."""
    resp = _client().messages.create(
        model=model(), max_tokens=max_tokens, system=system,
        output_config={"format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": user}],
    )
    return json.loads(_text(resp))
