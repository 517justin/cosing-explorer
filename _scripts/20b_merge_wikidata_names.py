#!/usr/bin/env python3
"""Merge the raw Wikidata cache into the shipped name files.

  _data/common_names.json    sp_zh/sp_en/fam_zh/fam_en (curated) + new sp_ja/fam_ja
                             Fill-only: existing entries are never overwritten.
  _data/compound_names.json  {inchikey: {"en": [<=3], "zh": [<=4], "ja": [<=5]}}

Traditional Chinese: zh-hant/zh-tw/zh-hk labels are used as-is; zh/zh-hans/zh-cn/zh-sg
are converted with OpenCC s2twp. Korean stays in the raw cache (no consumer yet).

Usage:
    .venv/bin/python _scripts/20b_merge_wikidata_names.py [--dry-run]
"""
import argparse
import json
import re
from pathlib import Path

import duckdb
from opencc import OpenCC

ROOT = Path(__file__).resolve().parent.parent
WD = ROOT / "_data" / "wikidata"
NAMES = ROOT / "_data" / "common_names.json"
CPD_NAMES = ROOT / "_data" / "compound_names.json"
DB = ROOT / "_data" / "kb.duckdb"

s2t = OpenCC("s2twp")
ZH_TRAD = ["zh-hant", "zh-tw", "zh-hk"]
ZH_SIMP = ["zh", "zh-hans", "zh-cn", "zh-sg"]
LATIN = re.compile(r"^[\x00-\x7f]+$")


def pools(rec, lang):
    """Candidate names for one language, best first: common name, label, aliases."""
    if lang == "zh":
        return dedupe(lang_candidates(rec, ZH_TRAD) + [s2t.convert(v) for v in lang_candidates(rec, ZH_SIMP)])
    return dedupe(lang_candidates(rec, [lang]))


def lang_candidates(rec, codes):
    out = []
    for code in codes:
        out += rec["c"].get(code, [])
        if code in rec["l"]:
            out.append(rec["l"][code])
        out += rec["a"].get(code, [])
    return out


def dedupe(seq):
    seen, out = set(), []
    for s in seq:
        s = s.strip()
        if s and s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out


def taxon_name(rec, lang, sci):
    """Single best common name for a taxon in `lang`, or None."""
    for v in pools(rec, lang):
        if v.lower() == sci.lower() or v.lower().startswith(sci.split()[0].lower() + " "):
            continue
        if lang in ("zh", "ja") and LATIN.match(v):
            continue
        if lang == "en":
            v = v[0].upper() + v[1:]
        return v
    return None


SYSTEMATIC = [
    re.compile(r"\d+,\d+"),
    re.compile(r"^\(?\d*[RSEZ]?[,\d]*\)?-"),
    re.compile(r"[\[\(]\d"),
    re.compile(r"\d[a-z]?-[a-z]"),
]


def systematic(name):
    return len(name) > 48 or any(p.search(name) for p in SYSTEMATIC)


def compound_names(rec, iupac):
    out = {}
    for lang, cap in (("en", 3), ("zh", 4), ("ja", 5)):
        plain, systematic_names = [], []
        for v in pools(rec, lang):
            if lang == "en" and v.lower() == (iupac or "").lower():
                continue
            if lang in ("zh", "ja") and LATIN.match(v):
                continue
            if len(v) > 40:
                continue
            (systematic_names if systematic(v) else plain).append(v)
        # zh/ja locant names (e.g. 反式-2-己烯醛) are real names: only a fallback, never en
        names = plain or (systematic_names if lang != "en" else [])
        if names:
            out[lang] = names[:cap]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    names = json.loads(NAMES.read_text("utf-8"))
    for k in ("sp_zh", "sp_en", "sp_ja", "fam_zh", "fam_en", "fam_ja"):
        names.setdefault(k, {})
    before = {k: len(v) for k, v in names.items()}

    for kind, prefix in (("species", "sp"), ("families", "fam")):
        cache = json.loads((WD / f"{kind}.json").read_text("utf-8"))
        for sci, rec in cache.items():
            if not rec:
                continue
            for lang in ("zh", "en", "ja"):
                key = f"{prefix}_{lang}"
                if sci in names[key]:
                    continue
                if prefix == "fam" and lang == "en":
                    continue
                v = taxon_name(rec, lang, sci)
                if v:
                    names[key][sci] = v

    cache = json.loads((WD / "compounds.json").read_text("utf-8"))
    db = duckdb.connect(str(DB), read_only=True)
    iupac = dict(db.execute("SELECT inchikey, iupac_name FROM compound_v2026").fetchall())
    db.close()
    cpd = {}
    for ik, rec in cache.items():
        if rec:
            n = compound_names(rec, iupac.get(ik))
            if n:
                cpd[ik] = n

    print("common_names.json:")
    for k, v in names.items():
        print(f"  {k:7s} {before[k]:5d} -> {len(v):5d}  (+{len(v) - before[k]})")
    langs = {l: sum(1 for v in cpd.values() if l in v) for l in ("en", "zh", "ja")}
    print(f"compound_names.json: {len(cpd):,} of {len(cache):,} compounds named  {langs}")

    if args.dry_run:
        return
    NAMES.write_text(json.dumps(names, ensure_ascii=False, indent=2, sort_keys=True), "utf-8")
    CPD_NAMES.write_text(json.dumps(cpd, ensure_ascii=False, separators=(",", ":"), sort_keys=True), "utf-8")
    print(f"wrote {NAMES.name}, {CPD_NAMES.name} ({CPD_NAMES.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
