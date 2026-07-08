"""Fetch Open Targets Platform evidence for the in-scope genes.

For each gene the ingestion records tractability, the count of safety liabilities,
and the genetic-association component of the target-disease association score for
the disease in scope (psoriasis by default). Symbols are resolved to Ensembl gene
identifiers through the Open Targets id-mapping query. Results are cached to
Parquet; the store reads them.

Run inside the project container::

    docker run --rm -v "$HOME/verdict:/app" verdict:latest \\
        python -m verdict.data.ingest_opentargets --genes TYK2 GATA3 TBX21 STAT3 CHD4 MED12
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

API = "https://api.platform.opentargets.org/api/v4/graphql"
SOURCE_DATASET = "OpenTargets"
SOURCE_FILE = "platform_graphql_v4"
PSORIASIS_EFO = "EFO_0000676"

DEFAULT_GENES = ["TYK2", "GATA3", "TBX21", "STAT3", "CHD4", "MED12", "AHR"]

_MAP = """query($terms:[String!]!){
  mapIds(queryTerms:$terms, entityNames:["target"]){
    mappings{ term hits{ id name entity } }
  }}"""

_TARGET = """query($ens:String!,$filter:String!){
  target(ensemblId:$ens){
    approvedSymbol
    tractability{ modality label value }
    safetyLiabilities{ event }
    associatedDiseases(BFilter:$filter){
      rows{ score datatypeScores{ id score } disease{ id name } }
    }
  }}"""


def _post(query: str, variables: dict) -> dict:
    r = requests.post(API, json={"query": query, "variables": variables}, timeout=60)
    r.raise_for_status()
    payload = r.json()
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]


def _resolve(genes: list[str]) -> dict[str, str]:
    data = _post(_MAP, {"terms": genes})
    out: dict[str, str] = {}
    for m in data["mapIds"]["mappings"]:
        for hit in m["hits"]:
            if hit["entity"] == "target":
                out[m["term"]] = hit["id"]
                break
    return out


def _target_record(symbol: str, ensembl: str, efo: str, disease_name: str) -> dict:
    t = _post(_TARGET, {"ens": ensembl, "filter": disease_name})["target"]
    approved = any(x["value"] and x["label"] == "Approved Drug" for x in t["tractability"])
    genetic = None
    rows = t["associatedDiseases"]["rows"]
    match = next((r for r in rows if r["disease"]["id"] == efo), rows[0] if rows else None)
    if match:
        for d in match["datatypeScores"]:
            if d["id"] == "genetic_association":
                genetic = d["score"]
    return {
        "gene_symbol": t["approvedSymbol"] or symbol,
        "ensembl": ensembl,
        "efo": efo,
        "tractability_approved_drug": bool(approved),
        "n_safety_liabilities": len(t["safetyLiabilities"]),
        "genetic_association_score": genetic,
    }


def ingest(genes: list[str], efo: str = PSORIASIS_EFO, disease_name: str = "psoriasis",
           out_dir: str = "data/store/opentargets") -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    mapping = _resolve(genes)
    records = []
    for symbol in genes:
        ensembl = mapping.get(symbol)
        if not ensembl:
            print(f"  {symbol}: no Open Targets mapping", flush=True)
            continue
        rec = _target_record(symbol, ensembl, efo, disease_name)
        records.append(rec)
        print(f"  {rec['gene_symbol']} ({ensembl}): approved_drug={rec['tractability_approved_drug']} "
              f"safety={rec['n_safety_liabilities']} genetic_assoc={rec['genetic_association_score']}",
              flush=True)
    table = pd.DataFrame.from_records(records)
    table.to_parquet(out / "opentargets.parquet", index=False)
    print(f"wrote opentargets.parquet ({len(table)} genes)", flush=True)

    manifest = {
        "source_dataset": SOURCE_DATASET, "source_file": SOURCE_FILE,
        "efo": efo, "genes": len(table), "built_at": datetime.now(timezone.utc).isoformat(),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch Open Targets evidence for the in-scope genes.")
    ap.add_argument("--genes", nargs="*", default=DEFAULT_GENES)
    ap.add_argument("--efo", default=PSORIASIS_EFO)
    ap.add_argument("--disease-name", default="psoriasis")
    ap.add_argument("--out", default="data/store/opentargets")
    args = ap.parse_args()
    ingest(args.genes, args.efo, args.disease_name, args.out)


if __name__ == "__main__":
    main()
