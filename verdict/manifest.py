"""atlas_manifest.built_from -- what the circularity check reads."""
from __future__ import annotations

BUILT_FROM: dict[str, str] = {
    "Zhu2025": "Marson_CRISPRi_genome_scale_CD4T_2025",
    "Moonen2026": "EMBL_TAPseq_Perturbseq_CD4T_2026",
    "DepMap": "Broad_DepMap_CRISPR",
    "OpenTargets": "OpenTargets_aggregated",
    "GTEx": "GTEx_bulk",
}


def screen_of(source_dataset: str) -> str | None:
    return BUILT_FROM.get(source_dataset)
