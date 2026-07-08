"""Maps check names to their run() callables. The selector picks from these."""
from __future__ import annotations
from . import direction, essentiality, selectivity_safety, circularity, range_scope, power

CHECKS = {
    m.name: m.run
    for m in (direction, essentiality, selectivity_safety, circularity, range_scope, power)
}
