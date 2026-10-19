#!/usr/bin/env python3
"""Structures from Wikidata for LOTUS compounds that PubChem does not know.

17_fetch_compound_smiles.py asks PubChem for every InChIKey in the LOTUS pairs and
records the ones it cannot resolve as {"not_found": true}. Those compounds drop out
of compound_v2026 and with them every species-compound link. LOTUS names the
Wikidata item of each structure (structure_wikidata), and Wikidata usually carries a
SMILES (P2017 isomeric, P233 canonical) for it.

  1. Fetch SMILES / formula / PubChem CID for the missing compounds from Wikidata
     (<=50 items per query, 2 s apart, resumable) into _data/wikidata/structures.json.
  2. Check each SMILES with RDKit: the InChIKey recomputed from it must equal the
     LOTUS key ("full"), or share its connectivity block ("planar": the same structure
     without stereochemistry). Anything else is rejected, so a wrong item cannot
     put a wrong structure on a compound.
  3. Write the accepted ones into _data/compound_cache.json in place of the
     not_found marker, tagged with source "wikidata".

Run 17_fetch_compound_smiles.py afterwards (nothing left to fetch, it just reloads
compound_v2026), then 18_render_structures.py and 19_compute_descriptors.py.

Usage:
    .venv/bin/python _scripts/17b_wikidata_structures.py [--limit N] [--no-fetch]
"""
import argparse
import csv
import gzip
import importlib.util
import json
import time
from pathlib import Path

import duckdb
from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, inchi, rdMolDescriptors

RDLogger.DisableLog("rdApp.*")

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "_data" / "kb.duckdb"
LOTUS = ROOT / "_data" / "lotus" / "lotus_260413.csv.gz"
COMPOUND_CACHE = ROOT / "_data" / "compound_cache.json"
RAW = ROOT / "_data" / "wikidata" / "structures.json"

_spec = importlib.util.spec_from_file_location("wd_names", ROOT / "_scripts" / "20_fetch_wikidata_names.py")
wd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wd)


def missing_keys(cache):
    con = duckdb.connect(str(DB), read_only=True)
    used = {r[0] for r in con.execute("SELECT DISTINCT inchikey FROM species_compounds_v2026").fetchall()}
    con.close()
    return sorted(ik for ik in used if cache.get(ik, {}).get("not_found"))


def lotus_qids(wanted):
    qids = {}
    with gzip.open(LOTUS, "rt", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            ik = r["structure_inchikey"]
            if ik in wanted and r["structure_wikidata"]:
                qids[ik] = r["structure_wikidata"].rsplit("/", 1)[-1]
    return qids


def query(qids):
    values = " ".join(f"wd:{q}" for q in qids)
    return f"""SELECT ?item ?ik ?iso ?can ?formula ?cid WHERE {{
  VALUES ?item {{ {values} }}
  OPTIONAL {{ ?item wdt:P235 ?ik }}
  OPTIONAL {{ ?item wdt:P2017 ?iso }}
  OPTIONAL {{ ?item wdt:P233 ?can }}
  OPTIONAL {{ ?item wdt:P274 ?formula }}
  OPTIONAL {{ ?item wdt:P662 ?cid }}
}}"""


def collect(bindings):
    out = {}
    for b in bindings:
        q = b["item"]["value"].rsplit("/", 1)[-1]
        rec = out.setdefault(q, {"ik": [], "iso": [], "can": [], "formula": [], "cid": []})
        for field in rec:
            if field in b and b[field]["value"] not in rec[field]:
                rec[field].append(b[field]["value"])
    return out


def fetch(todo, qids, raw, limit):
    keys = [ik for ik in todo if ik in qids and ik not in raw]
    if limit:
        keys = keys[:limit]
    print(f"{len(todo):,} compounds missing, {len(keys):,} to query on Wikidata "
          f"({sum(1 for ik in todo if ik not in qids)} have no Wikidata item in LOTUS)")
    for i in range(0, len(keys), wd.BATCH):
        batch = keys[i:i + wd.BATCH]
        bindings = wd.sparql(query([qids[ik] for ik in batch]))
        if bindings is None:
            print(f"  batch {i // wd.BATCH + 1}: FAILED, left uncached")
            continue
        found = collect(bindings)
        for ik in batch:
            raw[ik] = {"q": qids[ik], **found.get(qids[ik], {"ik": [], "iso": [], "can": [], "formula": [], "cid": []})}
        RAW.write_text(json.dumps(raw, ensure_ascii=False, separators=(",", ":")), "utf-8")
        with_smiles = sum(1 for ik in batch if raw[ik]["iso"] or raw[ik]["can"])
        print(f"  [{min(i + wd.BATCH, len(keys)):,}/{len(keys):,}] with a SMILES {with_smiles}/{len(batch)}")
        time.sleep(wd.INTERVAL)


def check(ik, rec):
    """First SMILES whose InChIKey matches, as (smiles, mol, 'full' | 'planar'), else None."""
    planar = None
    for smi in rec["iso"] + rec["can"]:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            continue
        try:
            key = inchi.MolToInchiKey(mol)
        except Exception:
            continue
        if key == ik:
            return smi, mol, "full"
        if planar is None and key and key.split("-")[0] == ik.split("-")[0]:
            planar = (smi, mol, "planar")
    return planar


def apply(todo, raw, cache):
    stats = {"full": 0, "planar": 0, "no_smiles": 0, "mismatch": 0, "not_queried": 0}
    for ik in todo:
        rec = raw.get(ik)
        if rec is None:
            stats["not_queried"] += 1
            continue
        if not (rec["iso"] or rec["can"]):
            stats["no_smiles"] += 1
            continue
        hit = check(ik, rec)
        if hit is None:
            stats["mismatch"] += 1
            continue
        smi, mol, match = hit
        cid = next((int(c) for c in rec["cid"] if c.isdigit()), None)
        cache[ik] = {
            "smiles": smi,
            "iupac": None,
            "formula": rdMolDescriptors.CalcMolFormula(mol),
            "mw": round(Descriptors.MolWt(mol), 2),
            "cid": cid,
            "source": "wikidata",
            "qid": rec["q"],
            "match": match,
        }
        stats[match] += 1
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="Max compounds to query (0=all)")
    ap.add_argument("--no-fetch", action="store_true", help="only apply the cached Wikidata results")
    args = ap.parse_args()

    cache = json.loads(COMPOUND_CACHE.read_text("utf-8"))
    todo = missing_keys(cache)
    raw = json.loads(RAW.read_text("utf-8")) if RAW.exists() else {}
    if not args.no_fetch:
        fetch(todo, lotus_qids(set(todo)), raw, args.limit)

    stats = apply(todo, raw, cache)
    COMPOUND_CACHE.write_text(json.dumps(cache, ensure_ascii=False, separators=(",", ":")), "utf-8")
    print(f"\nof {len(todo):,} missing compounds: {stats['full'] + stats['planar']:,} recovered "
          f"({stats['full']:,} exact InChIKey, {stats['planar']:,} same structure without stereochemistry); "
          f"{stats['no_smiles']:,} have no SMILES on Wikidata, {stats['mismatch']:,} SMILES rejected "
          f"because their InChIKey differs, {stats['not_queried']:,} not queried")


if __name__ == "__main__":
    main()
