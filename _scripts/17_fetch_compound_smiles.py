#!/usr/bin/env python3
"""Batch-fetch SMILES, IUPAC name, and formula from PubChem for all LOTUS compounds.

Strategy:
  1. Collect all unique InChIKeys from species_compounds_v2026.
  2. Subtract those already in compound_cache.json (resume-safe).
  3. POST batches of 100 InChIKeys to PubChem PUG REST.
  4. Write results to _data/compound_cache.json (append-friendly).
  5. At the end, load the cache into a DuckDB table `compound_v2026`.

PubChem rate limit: 5 requests/second, 400 InChIKeys/POST max.
We use 100 per batch for safety and set 0.25 s between requests.
"""
import json, time, sys, os
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import duckdb

DB   = Path(__file__).resolve().parent.parent / "_data" / "kb.duckdb"
CACHE = Path(__file__).resolve().parent.parent / "_data" / "compound_cache.json"
BATCH = 100
DELAY = 0.25  # seconds between requests

URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/inchikey/property/InChIKey,IsomericSMILES,IUPACName,MolecularFormula,MolecularWeight/JSON"


def load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text("utf-8"))
    return {}


def save_cache(cache):
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, separators=(",", ":")), "utf-8")


def fetch_batch(inchikeys):
    body = "inchikey=" + ",".join(inchikeys)
    req = Request(URL, data=body.encode("utf-8"), method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        rows = data.get("PropertyTable", {}).get("Properties", [])
        result = {}
        for row in rows:
            ik = row.get("InChIKey")
            if ik:
                result[ik] = {
                    "smiles": row.get("IsomericSMILES") or row.get("SMILES"),
                    "iupac":  row.get("IUPACName"),
                    "formula": row.get("MolecularFormula"),
                    "mw":     row.get("MolecularWeight"),
                    "cid":    row.get("CID"),
                }
        return result
    except HTTPError as e:
        if e.code == 404:
            return {}
        if e.code in (429, 500, 502, 503, 504):
            return None  # transient, retry later
        raise
    except (URLError, TimeoutError):
        return None


def main():
    db = duckdb.connect(str(DB), read_only=True)
    all_iks = sorted(
        r[0]
        for r in db.execute(
            "SELECT DISTINCT inchikey FROM species_compounds_v2026"
        ).fetchall()
    )
    db.close()

    cache = load_cache()
    todo = [ik for ik in all_iks if ik not in cache]
    print(f"Total compounds: {len(all_iks):,}")
    print(f"Already cached:  {len(cache):,}")
    print(f"To fetch:        {len(todo):,}")

    if not todo:
        print("Nothing to fetch.")
        load_into_db(cache)
        return

    batches = [todo[i : i + BATCH] for i in range(0, len(todo), BATCH)]
    print(f"Batches: {len(batches)} x {BATCH}")

    found = 0
    not_found = 0
    errors = 0
    save_interval = 50  # save cache every N batches

    for i, batch in enumerate(batches):
        result = fetch_batch(batch)
        if result is None:
            errors += 1
            for wait in (5, 15, 30):
                print(f"  [{i+1}/{len(batches)}] transient error, retrying in {wait}s...")
                time.sleep(wait)
                result = fetch_batch(batch)
                if result is not None:
                    break
            if result is None:
                print(f"  [{i+1}/{len(batches)}] still failing, marking batch as not_found")
                for ik in batch:
                    cache[ik] = {"not_found": True}
                not_found += len(batch)
                continue

        for ik in batch:
            if ik in result:
                cache[ik] = result[ik]
                found += 1
            else:
                cache[ik] = {"not_found": True}
                not_found += 1

        if (i + 1) % 10 == 0 or i == len(batches) - 1:
            pct = (i + 1) / len(batches) * 100
            print(f"  [{i+1}/{len(batches)}] {pct:.1f}%  found={found}  miss={not_found}  err={errors}")

        if (i + 1) % save_interval == 0:
            save_cache(cache)

        time.sleep(DELAY)

    save_cache(cache)
    print(f"\nDone. Found={found}, NotFound={not_found}, Errors={errors}")
    print(f"Cache size: {len(cache):,} entries")

    load_into_db(cache)


def load_into_db(cache):
    db = duckdb.connect(str(DB))
    db.execute("DROP TABLE IF EXISTS compound_v2026")
    db.execute("""
        CREATE TABLE compound_v2026 (
            inchikey   VARCHAR PRIMARY KEY,
            smiles     VARCHAR,
            iupac_name VARCHAR,
            formula    VARCHAR,
            mw         DOUBLE,
            cid        BIGINT
        )
    """)
    rows = []
    for ik, v in cache.items():
        if v.get("not_found"):
            continue
        rows.append((
            ik,
            v.get("smiles"),
            v.get("iupac"),
            v.get("formula"),
            v.get("mw"),
            v.get("cid"),
        ))
    if rows:
        db.executemany(
            "INSERT INTO compound_v2026 VALUES (?,?,?,?,?,?)", rows
        )
    n = db.execute("SELECT count(*) FROM compound_v2026").fetchone()[0]
    db.close()
    print(f"Loaded {n:,} compounds into compound_v2026")


if __name__ == "__main__":
    main()
