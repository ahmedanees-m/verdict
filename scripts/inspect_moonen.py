"""Inspect the Moonen supplementary tables to locate the trace tables.

Reports each sheet's shape and columns and whether TYK2 appears, to identify the
CRE-gene pair table and the variant-to-CRE table before building the trace.
"""
from __future__ import annotations

import glob

import pandas as pd

for path in sorted(glob.glob("data/raw/moonen/*.xlsx")):
    try:
        xl = pd.ExcelFile(path)
    except Exception as e:  # noqa: BLE001
        print(f"{path}: ERROR {e}")
        continue
    for sheet in xl.sheet_names:
        try:
            df = xl.parse(sheet)
        except Exception as e:  # noqa: BLE001
            print(f"{path} [{sheet}]: parse error {e}")
            continue
        as_str = df.astype(str)
        has_tyk2 = as_str.apply(lambda c: c.str.contains("TYK2", case=False, na=False)).any().any()
        has_psor = as_str.apply(lambda c: c.str.contains("psorias", case=False, na=False)).any().any()
        cols = [str(c) for c in df.columns][:10]
        print(f"{path.split('/')[-1]} [{sheet}]: {df.shape} tyk2={has_tyk2} psoriasis={has_psor}")
        print(f"    cols: {cols}")
