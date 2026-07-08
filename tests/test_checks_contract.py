"""Interface contract + the pure-logic gates that need no data."""
from verdict.checks.base import Claim, Status
from verdict.checks import direction, circularity, range_scope
from verdict.checks.registry import CHECKS


def test_all_checks_return_checkresult_on_bare_claim():
    claim = Claim(text="bare")
    for run in CHECKS.values():
        res = run(claim, store=None)
        assert res.status in Status


def test_direction_context_match_gate_blocks_non_cd4():
    # claim about macrophages must NOT fire direction -> routes to range_scope
    claim = Claim(text="Z promotes P in macrophages", cell_type="macrophage",
                  direction="promotes", scope="cell_type_specific")
    res = direction.run(claim, store=None)
    assert res.status is Status.INSUFFICIENT
    assert "range_scope" in res.rationale


def test_circularity_fires_on_shared_provenance():
    # cited source == validating atlas (Zhu2025) -> CIRCULAR
    claim = Claim(text="...", cited_source="Zhu2025")
    res = circularity.run(claim, store=None)
    assert res.status is Status.FIRED


def test_range_scope_fires_on_organism_wide():
    claim = Claim(text="...", scope="organism_wide")
    res = range_scope.run(claim, store=None)
    assert res.status is Status.FIRED
