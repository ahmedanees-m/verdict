"""Per-check firing behaviour against a controlled store.

Each check is exercised for its firing case, a non-firing case, and the
insufficient-on-missing-data case, using a fake store that returns receipted
values so the tests need no ingested atlas.
"""
from verdict.checks.base import Claim, Status
from verdict.checks import direction, essentiality, selectivity_safety, power
from verdict.receipts import NO_RECEIPT
from tests.helpers import gated


class FakeStore:
    """Returns configured values for the store methods a check calls."""

    def __init__(self, **values):
        self._v = values

    def zhu_effect(self, gene, program_genes, condition):
        return self._v.get("zhu_effect", NO_RECEIPT)

    def zhu_gene_effects(self, gene, program_genes, condition):
        return self._v.get("zhu_gene_effects", [])

    def zhu_power(self, gene, condition):
        return self._v.get("zhu_power", NO_RECEIPT)

    def zhu_breadth(self, gene, condition):
        return self._v.get("zhu_breadth", NO_RECEIPT)

    def zhu_summary(self, gene, condition):
        return self._v.get("zhu_summary", NO_RECEIPT)

    def depmap_essentiality(self, gene):
        return self._v.get("depmap_essentiality", NO_RECEIPT)

    def expression_breadth(self, gene):
        return self._v.get("expression_breadth", NO_RECEIPT)

    def opentargets(self, gene):
        return self._v.get("opentargets", NO_RECEIPT)


def _effect(mean_lfc, n_genes=10, n_sig=5):
    return {"mean_log_fc": gated(mean_lfc), "mean_zscore": gated(mean_lfc),
            "n_genes": gated(n_genes), "n_significant": gated(n_sig)}


def _promotes_claim():
    return Claim(text="X promotes Th17", gene="X", program="Th17", direction="promotes",
                 scope="cell_type_specific", cell_type="CD4+ T", condition="Stim8hr")


# ---- direction ----
def test_direction_fires_on_opposite_effect():
    store = FakeStore(zhu_effect=_effect(0.8), zhu_power=gated(0.5))
    res = direction.run(_promotes_claim(), store)
    assert res.status is Status.FIRED


def test_direction_not_fired_when_consistent():
    store = FakeStore(zhu_effect=_effect(-0.8), zhu_power=gated(0.5))
    res = direction.run(_promotes_claim(), store)
    assert res.status is Status.NOT_FIRED


def test_direction_insufficient_when_underpowered():
    store = FakeStore(zhu_effect=_effect(0.8), zhu_power=gated(0.1))
    res = direction.run(_promotes_claim(), store)
    assert res.status is Status.INSUFFICIENT


def test_direction_insufficient_on_missing_data():
    res = direction.run(_promotes_claim(), FakeStore())
    assert res.status is Status.INSUFFICIENT


def test_direction_insufficient_on_nan_crossguide():
    store = FakeStore(zhu_effect=_effect(0.8), zhu_power=gated(float("nan")))
    res = direction.run(_promotes_claim(), store)
    assert res.status is Status.INSUFFICIENT


# ---- essentiality ----
def _selective_claim():
    return Claim(text="X selectively regulates Th2", gene="X", program="Th2",
                 scope="selective", cell_type="CD4+ T", condition="Stim8hr")


def _ess(common, median, frac=0.95):
    return {"common_essential": gated(common), "chronos_median": gated(median),
            "frac_dependent": gated(frac)}


def test_essentiality_fires_on_essential_and_broad():
    store = FakeStore(depmap_essentiality=_ess(1, -1.2), zhu_breadth=gated(0.99))
    res = essentiality.run(_selective_claim(), store)
    assert res.status is Status.FIRED


def test_essentiality_not_fired_when_specific_regulator():
    # essential-looking but not broadly essential, high breadth: not flagged (GATA3-like)
    store = FakeStore(depmap_essentiality=_ess(0, 0.1), zhu_breadth=gated(0.99))
    res = essentiality.run(_selective_claim(), store)
    assert res.status is Status.NOT_FIRED


def test_essentiality_not_fired_when_not_broad():
    store = FakeStore(depmap_essentiality=_ess(1, -1.2), zhu_breadth=gated(0.2))
    res = essentiality.run(_selective_claim(), store)
    assert res.status is Status.NOT_FIRED


def test_essentiality_insufficient_on_missing_data():
    res = essentiality.run(_selective_claim(), FakeStore())
    assert res.status is Status.INSUFFICIENT


def test_essentiality_not_fired_without_selectivity():
    claim = Claim(text="X regulates Th2", gene="X", program="Th2", scope="cell_type_specific")
    res = essentiality.run(claim, FakeStore())
    assert res.status is Status.NOT_FIRED


# ---- selectivity_safety ----
def _safety_claim(cell_type="CD4+ T"):
    return Claim(text="X is safe because activation-restricted", gene="X", disease="psoriasis",
                 scope="organism_wide", cell_type=cell_type, asserts_safety=True)


def test_selectivity_safety_fires_on_organism_wide_safety():
    store = FakeStore(expression_breadth=gated(0.75))
    res = selectivity_safety.run(_safety_claim(), store)
    assert res.status is Status.FIRED


def test_selectivity_safety_insufficient_off_cd4():
    res = selectivity_safety.run(_safety_claim(cell_type="all immune cell types"), FakeStore())
    assert res.status is Status.INSUFFICIENT


def test_selectivity_safety_not_fired_without_safety_verb():
    claim = Claim(text="X regulates Th17", gene="X", scope="cell_type_specific")
    res = selectivity_safety.run(claim, FakeStore())
    assert res.status is Status.NOT_FIRED


# ---- power ----
def _power_claim():
    return Claim(text="X", gene="X", cell_type="CD4+ T", condition="Stim8hr")


def test_power_fires_on_weak_support():
    store = FakeStore(zhu_summary={"guide_correlation_signif": gated(0.1),
                                   "n_cells_target": gated(100)})
    res = power.run(_power_claim(), store)
    assert res.status is Status.FIRED


def test_power_not_fired_on_adequate_support():
    store = FakeStore(zhu_summary={"guide_correlation_signif": gated(0.6),
                                   "n_cells_target": gated(500)})
    res = power.run(_power_claim(), store)
    assert res.status is Status.NOT_FIRED


def test_power_insufficient_on_missing_data():
    res = power.run(_power_claim(), FakeStore())
    assert res.status is Status.INSUFFICIENT
