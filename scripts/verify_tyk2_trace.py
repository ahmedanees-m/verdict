"""Verify the Moonen TYK2 trace and program-gene coverage before the network view.

Checks which Moonen table carries significant CRE-gene links, the TYK2 target-gene
call and its disease traits, and whether the interferon program markers are among
the Zhu measured genes.
"""
from __future__ import annotations

import glob

import pandas as pd

from verdict.store import Store

SIG = ("signif", "padj", "pval", "fdr", "log2fc", "logfc", "effect", "beta", "zscore", "score")

print("=== Moonen tables ===")
for path in sorted(glob.glob("data/raw/moonen/*.xlsx")):
    xl = pd.ExcelFile(path)
    legend = ""
    if "Legend" in xl.sheet_names:
        try:
            legend = str(xl.parse("Legend").columns[0])
        except Exception:
            pass
    for sheet in xl.sheet_names:
        if sheet == "Legend":
            continue
        df = xl.parse(sheet)
        sig_cols = [str(c) for c in df.columns if any(s in str(c).lower() for s in SIG)]
        has_tyk2 = df.astype(str).apply(lambda c: c.str.contains("TYK2", case=False, na=False)).any().any()
        print(f"{path.split('/')[-1]} [{sheet}] {df.shape} tyk2={has_tyk2} sig_cols={sig_cols}")
        if legend:
            print(f"    legend: {legend}")

print("\n=== media-4 prioritization_source distribution ===")
m4 = pd.read_excel("data/raw/moonen/media-4.xlsx", sheet_name="prioritised_gene_list")
print(m4["prioritization_source"].value_counts().to_string())
tyk2 = m4[m4["gene_name"].astype(str) == "TYK2"]
print(f"\nTYK2 rows: {len(tyk2)}; traits: {sorted(tyk2['SNP_trait'].astype(str).unique())}")
pso = tyk2[tyk2["SNP_trait"].astype(str).str.contains('soria', case=False, na=False)]
print("TYK2 psoriasis rows:")
print(pso.to_string(index=False))

print("\n=== TYK2-neighbour target-gene check (which genes does the chr19 CRE assign to?) ===")
cre = pso["peak"].iloc[0] if not pso.empty else None
if cre is not None:
    same_cre = m4[m4["peak"].astype(str) == str(cre)]
    print(f"CRE {cre} assigns to genes: {sorted(same_cre['gene_name'].astype(str).unique())}")

print("\n=== program-gene coverage in Zhu measured genes ===")
store = Store()
groups = {
    "IFN": ["MX1", "MX2", "OAS1", "OAS2", "OAS3", "ISG15", "IFI6", "IFI44", "IFI44L",
            "IFITM1", "IFIT1", "IFIT3", "STAT1", "STAT2", "IRF7", "IRF9"],
}
for name, genes in groups.items():
    measured = {sym for _, sym in store._gene_codes(genes)}
    hit = [g for g in genes if g in measured]
    miss = [g for g in genes if g not in measured]
    print(f"{name}: {len(hit)}/{len(genes)} measured; missing={miss}")
