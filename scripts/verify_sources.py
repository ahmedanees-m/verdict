"""Validate live access and content for the external data sources.

Probes Open Targets (GraphQL), GTEx, the Human Protein Atlas, and the DepMap
download index against TYK2 (ENSG00000105397) as a known reference gene. Prints
what each source returns so the values can be sanity-checked before ingestion.
"""
from __future__ import annotations

import requests

OT = "https://api.platform.opentargets.org/api/v4/graphql"
TYK2 = "ENSG00000105397"
PSORIASIS_EFO = "EFO_0000676"


def opentargets_target() -> None:
    q = """query($ens:String!){
      target(ensemblId:$ens){
        approvedSymbol biotype
        tractability{ modality label value }
        safetyLiabilities{ event datasource }
      }}"""
    r = requests.post(OT, json={"query": q, "variables": {"ens": TYK2}}, timeout=45)
    t = r.json()["data"]["target"]
    trac = [(x["modality"], x["label"]) for x in t["tractability"] if x["value"]]
    events = sorted({s["event"] for s in t["safetyLiabilities"] if s.get("event")})
    print(f"[OpenTargets target] http {r.status_code}")
    print(f"  approvedSymbol={t['approvedSymbol']} biotype={t['biotype']}")
    print(f"  tractability(true)={trac[:8]}")
    print(f"  safetyLiabilities n={len(t['safetyLiabilities'])} events={events[:8]}")


def opentargets_assoc() -> None:
    q = """query($ens:String!,$efo:String!){
      target(ensemblId:$ens){
        associatedDiseases(efoIds:[$efo]){
          count rows{ score datatypeScores{ id score } disease{ id name } }
        }}}"""
    r = requests.post(OT, json={"query": q, "variables": {"ens": TYK2, "efo": PSORIASIS_EFO}}, timeout=45)
    ad = r.json()["data"]["target"]["associatedDiseases"]
    print(f"[OpenTargets assoc] http {r.status_code} count={ad['count']}")
    for row in ad["rows"]:
        gen = [d["score"] for d in row["datatypeScores"] if d["id"] == "genetic_association"]
        print(f"  {row['disease']['name']} ({row['disease']['id']}): overall={row['score']:.3f} "
              f"genetic_association={gen[0]:.3f}" if gen else
              f"  {row['disease']['name']}: overall={row['score']:.3f}")


def gtex_gene() -> None:
    r = requests.get("https://gtexportal.org/api/v2/reference/gene",
                     params={"geneId": "TYK2"}, timeout=45)
    data = r.json().get("data", [])
    print(f"[GTEx gene] http {r.status_code} rows={len(data)}")
    for g in data[:2]:
        print(f"  gencodeId={g.get('gencodeId')} symbol={g.get('geneSymbol')} chrom={g.get('chromosome')}")


def hpa_gene() -> None:
    r = requests.get(f"https://www.proteinatlas.org/{TYK2}.json", timeout=45)
    if r.status_code != 200:
        print(f"[HPA] http {r.status_code}")
        return
    j = r.json()
    tissue_keys = [k for k in j if "issue" in k.lower() or "RNA" in k]
    print(f"[HPA] http {r.status_code} symbol={j.get('Gene')} keys={tissue_keys[:8]}")


def depmap_index() -> None:
    r = requests.get("https://depmap.org/portal/api/download/downloads", timeout=90)
    d = r.json()
    releases = d.get("releaseData") or d.get("releases") or []
    names = [x.get("releaseName") or x.get("name") for x in releases]
    print(f"[DepMap index] http {r.status_code} releases={names[:6]}")
    table = d.get("table") or d.get("downloads") or []
    for f in table:
        fn = f.get("fileName", "")
        if "CRISPRGeneEffect" in fn or "CommonEssential" in fn:
            print(f"  {f.get('releaseName')} :: {fn} :: {str(f.get('downloadUrl',''))[:90]}")


def main() -> None:
    for label, fn in [
        ("opentargets_target", opentargets_target),
        ("opentargets_assoc", opentargets_assoc),
        ("gtex_gene", gtex_gene),
        ("hpa_gene", hpa_gene),
        ("depmap_index", depmap_index),
    ]:
        try:
            fn()
        except Exception as e:  # noqa: BLE001 - validation probe, report and continue
            print(f"[{label}] ERROR: {type(e).__name__}: {e}")
        print()


if __name__ == "__main__":
    main()
