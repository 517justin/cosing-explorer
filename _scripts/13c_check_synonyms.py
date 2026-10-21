#!/usr/bin/env python3
"""Check GBIF synonyms against GBIF's own name matching before 13_lotus.py uses them.

A synonym list holds names, not taxa: "Annona glabra" is listed among the synonyms
of Annona squamosa (an older homonym by another author) although GBIF's accepted
Annona glabra L. is a different species, and LOTUS means the accepted one. Crediting
its compounds to Annona squamosa would be wrong.

For every synonym name that LOTUS actually uses, ask GBIF's match service what the
bare name means. 13_lotus.py then keeps the synonym only when the answer is an exact
match to a synonym whose accepted taxon is the project species in question.

Needs lotus_pair, so run 13_lotus.py once first (without this cache it ignores all
synonyms), then this script, then 13_lotus.py again.

Usage:
    .venv/bin/python _scripts/13c_check_synonyms.py
"""
import importlib.util
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from common import DATA, ROOT, connect

SYNONYMS = DATA / "gbif_synonyms.json"
CHECK = DATA / "gbif_synonym_check.json"
API = "https://api.gbif.org/v1/species/match?name={}"
FIELDS = ("matchType", "status", "acceptedUsageKey", "usageKey", "rank", "scientificName")
WORKERS = 4

_spec = importlib.util.spec_from_file_location("lotus13", ROOT / "_scripts" / "13_lotus.py")
lotus13 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lotus13)


def match(name, tries=5):
    req = urllib.request.Request(API.format(urllib.parse.quote(name)), headers={"User-Agent": "cosing-kg/0.1"})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as fh:
                data = json.load(fh)
            return {k: data.get(k) for k in FIELDS}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(3 * (attempt + 1))
    return None


def used_synonym_names(con):
    """Synonym names (original spelling) that match an organism in LOTUS."""
    syn = json.loads(SYNONYMS.read_text("utf-8"))
    con.execute("CREATE OR REPLACE TEMP TABLE syn (alias VARCHAR, alias_norm VARCHAR)")
    con.executemany("INSERT INTO syn (alias) VALUES (?)", [(n,) for n in {n for v in syn.values() for n, _ in v}])
    con.execute(f"UPDATE syn SET alias_norm = {lotus13.norm('alias')}")
    return sorted(r[0] for r in con.execute(
        "SELECT alias FROM syn WHERE alias_norm IN (SELECT DISTINCT organism_norm FROM lotus_pair)").fetchall())


def main():
    if not SYNONYMS.exists():
        raise SystemExit(f"missing {SYNONYMS.name}, run 13b_gbif_synonyms.py first")
    con = connect()
    names = used_synonym_names(con)
    con.close()
    cache = json.loads(CHECK.read_text("utf-8")) if CHECK.exists() else {}
    todo = [n for n in names if n not in cache]
    print(f"{len(names):,} synonym names occur in LOTUS, {len(names) - len(todo):,} checked already, {len(todo):,} to check")
    failed = 0
    with ThreadPoolExecutor(WORKERS) as pool:
        for i in range(0, len(todo), 100):
            batch = todo[i:i + 100]
            for name, res in zip(batch, pool.map(match, batch)):
                if res is None:
                    failed += 1
                else:
                    cache[name] = res
            CHECK.write_text(json.dumps(cache, ensure_ascii=False, separators=(",", ":"), sort_keys=True), "utf-8")
            print(f"  [{min(i + 100, len(todo)):,}/{len(todo):,}]")
    accepted = sum(1 for v in cache.values() if v["status"] == "ACCEPTED")
    exact_syn = sum(1 for v in cache.values() if v["matchType"] == "EXACT" and v["status"] != "ACCEPTED")
    print(f"\n{len(cache):,} names checked: {exact_syn:,} resolve to a synonym, {accepted:,} are accepted species "
          f"in their own right, {failed} lookups failed")


if __name__ == "__main__":
    main()
