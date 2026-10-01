#!/usr/bin/env python3
"""Fetch multilingual names from Wikidata (en/zh/ja/ko) into a resumable cache.

  species    P225 (taxon name)  -> labels, aliases, P1843 (taxon common name)
  families   P225 (taxon name)  -> labels, aliases, P1843
  compounds  P235 (InChIKey)    -> labels, aliases

Raw results (language tags untouched, no s2t conversion) go to
_data/wikidata/{kind}.json as {key: record | null}. null = queried, no hit.
Merging into the shipped name files is done by 20b_merge_wikidata_names.py.

Etiquette: <=50 keys/query, 2 s between queries, descriptive User-Agent,
Retry-After honoured on 429.

Usage:
    .venv/bin/python _scripts/20_fetch_wikidata_names.py species|families|compounds [--limit N] [--all]
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "_data" / "kb.duckdb"
CACHE_DIR = ROOT / "_data" / "wikidata"
ENDPOINT = "https://query.wikidata.org/sparql"
UA = "cosing-explorer/0.1 (https://github.com/517justin/cosing-explorer; justintp6@gmail.com)"
BATCH = 50
INTERVAL = 2.0
LANGS = ["en", "ja", "ko", "zh", "zh-hant", "zh-tw", "zh-hk", "zh-hans", "zh-cn", "zh-sg"]
LANG_FILTER = ", ".join(f'"{l}"' for l in LANGS)


def sparql(query, tries=5):
    data = urllib.parse.urlencode({"query": query}).encode()
    req = urllib.request.Request(
        ENDPOINT, data=data,
        headers={"User-Agent": UA, "Accept": "application/sparql-results+json"},
    )
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)["results"]["bindings"]
        except urllib.error.HTTPError as e:
            wait = int(e.headers.get("Retry-After", 0) or 0) if e.code == 429 else 0
            wait = max(wait, 5 * (attempt + 1))
            print(f"    HTTP {e.code}, retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            wait = 5 * (attempt + 1)
            print(f"    {type(e).__name__}: {e}, retry in {wait}s", file=sys.stderr)
            time.sleep(wait)
    return None


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_query(kind, keys):
    values = " ".join(f'"{esc(k)}"' for k in keys)
    prop = "wdt:P235" if kind == "compounds" else "wdt:P225"
    common = (
        '\n    UNION { ?item wdt:P1843 ?text . BIND("c" AS ?kind) }' if kind != "compounds" else ""
    )
    return f"""SELECT ?key ?item ?kind ?text WHERE {{
  VALUES ?key {{ {values} }}
  ?item {prop} ?key .
  {{ ?item rdfs:label ?text . BIND("l" AS ?kind) }}
  UNION {{ ?item skos:altLabel ?text . BIND("a" AS ?kind) }}{common}
  FILTER(lang(?text) IN ({LANG_FILTER}))
}}"""


def collect(bindings):
    """Group bindings into {key: record}; keep the best item when a key matches several."""
    items = {}
    for b in bindings:
        key = b["key"]["value"]
        qid = b["item"]["value"].rsplit("/", 1)[-1]
        rec = items.setdefault(key, {}).setdefault(qid, {"l": {}, "a": {}, "c": {}})
        lang, text = b["text"]["xml:lang"], b["text"]["value"]
        kind = b["kind"]["value"]
        if kind == "l":
            rec["l"][lang] = text
        else:
            bucket = rec["a" if kind == "a" else "c"].setdefault(lang, [])
            if text not in bucket:
                bucket.append(text)
    out = {}
    for key, cands in items.items():
        def richness(r):
            return len(r["l"]) + sum(map(len, r["a"].values())) + sum(map(len, r["c"].values()))
        qid, rec = max(cands.items(), key=lambda kv: richness(kv[1]))
        rec["q"] = qid
        if len(cands) > 1:
            rec["multi"] = sorted(cands)
        out[key] = rec
    return out


def load_keys(kind, include_all):
    db = duckdb.connect(str(DB), read_only=True)
    if kind == "species":
        rows = db.execute(
            "SELECT DISTINCT species_accepted FROM extract_v2026 WHERE species_accepted IS NOT NULL"
        ).fetchall()
    elif kind == "families":
        rows = db.execute(
            "SELECT DISTINCT COALESCE(family_final, family_accepted) FROM extract_v2026 "
            "WHERE COALESCE(family_final, family_accepted) IS NOT NULL"
        ).fetchall()
    elif include_all:
        rows = db.execute("SELECT inchikey FROM compound_v2026").fetchall()
    else:
        rows = db.execute(
            "SELECT sc.inchikey FROM species_compounds_v2026 sc "
            "JOIN compound_v2026 c ON sc.inchikey = c.inchikey "
            "GROUP BY 1 HAVING count(DISTINCT sc.species) >= 2"
        ).fetchall()
    db.close()
    return sorted(r[0] for r in rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["species", "families", "compounds"])
    ap.add_argument("--limit", type=int, default=0, help="Max uncached keys to query (0=all)")
    ap.add_argument("--all", action="store_true", help="compounds: all InChIKeys, not just Explorer set")
    args = ap.parse_args()

    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = CACHE_DIR / f"{args.kind}.json"
    cache = json.loads(cache_path.read_text("utf-8")) if cache_path.exists() else {}

    keys = load_keys(args.kind, args.all)
    todo = [k for k in keys if k not in cache]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{args.kind}: {len(keys):,} keys, {len(keys) - len(todo):,} cached, {len(todo):,} to query")

    failed = 0
    for i in range(0, len(todo), BATCH):
        batch = todo[i : i + BATCH]
        bindings = sparql(build_query(args.kind, batch))
        if bindings is None:
            failed += len(batch)
            print(f"  batch {i // BATCH + 1}: FAILED ({len(batch)} keys left uncached)")
            continue
        found = collect(bindings)
        for k in batch:
            cache[k] = found.get(k)
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, separators=(",", ":")), "utf-8")
        hits = sum(1 for k in batch if found.get(k))
        print(f"  [{min(i + BATCH, len(todo)):,}/{len(todo):,}] hits {hits}/{len(batch)}")
        time.sleep(INTERVAL)

    hit_total = sum(1 for k in keys if cache.get(k))
    print(f"\nDone. cached={len([k for k in keys if k in cache]):,} hits={hit_total:,} failed_batches_keys={failed}")


if __name__ == "__main__":
    main()
