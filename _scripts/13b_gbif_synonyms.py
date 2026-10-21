#!/usr/bin/env python3
"""GBIF synonyms of every accepted species in the project, for the LOTUS join.

LOTUS names organisms with its own taxonomy, so a compound can be filed under a
name GBIF treats as a synonym ("Vetiveria zizanioides" for "Chrysopogon
zizanioides"). 13_lotus.py reads _data/gbif_synonyms.json to attribute those
reports to the accepted species.

Only SYNONYM, HOMOTYPIC_SYNONYM and HETEROTYPIC_SYNONYM are kept. PROPARTE_SYNONYM
and MISAPPLIED names belong to more than one taxon (or to a different one), and
attributing their compounds would be wrong.

Usage:
    .venv/bin/python _scripts/13b_gbif_synonyms.py [--limit N]
"""
import argparse
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import duckdb

from common import DATA

CACHE = DATA / "gbif_synonyms.json"
API = "https://api.gbif.org/v1/species/{key}/synonyms?limit=1000&offset={offset}"
KEEP = {"SYNONYM", "HOMOTYPIC_SYNONYM", "HETEROTYPIC_SYNONYM"}
WORKERS = 4


def get(url, tries=5):
    req = urllib.request.Request(url, headers={"User-Agent": "cosing-kg/0.1"})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as fh:
                return json.load(fh)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"results": [], "endOfRecords": True}
            wait = 3 * (attempt + 1)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            wait = 3 * (attempt + 1)
        time.sleep(wait)
    return None


def synonyms(key):
    """[[canonical name, status], ...] for one accepted GBIF key, None if GBIF kept failing."""
    out, offset = [], 0
    while True:
        page = get(API.format(key=key, offset=offset))
        if page is None:
            return None
        for r in page.get("results", []):
            name = r.get("canonicalName")
            if name and r.get("taxonomicStatus") in KEEP:
                out.append([name, r["taxonomicStatus"]])
        if page.get("endOfRecords", True):
            return sorted({tuple(x) for x in out})
        offset += 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="Max species to query (0=all)")
    args = ap.parse_args()

    con = duckdb.connect(str(DATA / "kb.duckdb"), read_only=True)
    keys = dict(con.execute(
        "SELECT species_accepted, any_value(gbif_key) FROM extract_v2026 "
        "WHERE species_accepted IS NOT NULL AND gbif_key IS NOT NULL GROUP BY 1 ORDER BY 1").fetchall())
    con.close()

    cache = json.loads(CACHE.read_text("utf-8")) if CACHE.exists() else {}
    todo = [sp for sp in keys if sp not in cache]
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(keys):,} species, {len(keys) - len(todo):,} cached, {len(todo):,} to query")

    done = 0
    with ThreadPoolExecutor(WORKERS) as pool:
        for i in range(0, len(todo), 100):
            batch = todo[i:i + 100]
            for sp, syn in zip(batch, pool.map(lambda s: synonyms(keys[s]), batch)):
                if syn is not None:
                    cache[sp] = [list(x) for x in syn]
                    done += 1
            CACHE.write_text(json.dumps(cache, ensure_ascii=False, separators=(",", ":"), sort_keys=True), "utf-8")
            print(f"  [{min(i + 100, len(todo)):,}/{len(todo):,}] cached {done:,}")
    total = sum(len(v) for v in cache.values())
    print(f"\nDone. {len(cache):,} species cached, {total:,} synonyms, {len(todo) - done} species failed")


if __name__ == "__main__":
    main()
