"""Load the pre-registered EVAL_SET.yaml."""
from __future__ import annotations
from pathlib import Path
import yaml


def load(path: str | Path = "EVAL_SET.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def cases(path: str | Path = "EVAL_SET.yaml") -> list[dict]:
    return load(path).get("cases", [])
