"""Phase 1d - settle the outstanding INCI-vs-description conflicts against GBIF.

For each undecided row in conflicts.csv both candidate binomials are looked up
in the GBIF backbone and reduced to their *accepted* species name. Then:

  same accepted name      -> the two spellings are the same taxon (one is a
                             synonym of the other). Resolve to the accepted name.
  different accepted names-> COSING really does name two different species in
                             one row. GBIF cannot say which was intended, so the
                             row is EXCLUDED rather than guessed at.
  neither matches         -> excluded.

Excluded rows stay in `ingredient` (the ingredient exists) but carry no species,
genus or family link, so they never enter the taxonomic graph.

Responses are cached in _data/gbif_cache.json so re-runs work offline and the
lookup date is recorded - GBIF's backbone changes as APG is revised.
"""

import csv
import datetime
import sys
import urllib.error

import gbif
from common import CORRECTIONS, conflicts_file

MIN_CONFIDENCE = 90


def accepted_species(rec):
    """(accepted_species, status, matchType, confidence) via the shared guards."""
    a = gbif.accepted(rec)
    if not a["ok"]:
        return None, a["reason"] or "NO_MATCH", a["match_type"] or "NONE", a["confidence"]
    return a["accepted_name"], a["status"], a["match_type"], a["confidence"]


def main():
    path = CORRECTIONS / conflicts_file()
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    cache = gbif.load_cache()

    # Re-evaluate rows this script decided before (so improved matching logic
    # takes effect on a re-run) but never overwrite a human 'manual' decision.
    OWNED = {"", "gbif", "excluded"}
    todo = [r for r in rows if r["resolution"] in OWNED]
    if not todo:
        print("no undecided conflicts")
        return
    print(f"resolving {len(todo)} conflicts against GBIF\n")

    resolved = excluded = 0
    for r in todo:
        inci = f"{r['inci_genus']} {r['inci_species']}".strip()
        desc = f"{r['desc_genus']} {r['desc_species']}".strip()

        a = accepted_species(gbif.lookup(inci, cache)) if r["inci_genus"] else (None, "NO_NAME", "NONE", 0)
        b = accepted_species(gbif.lookup(desc, cache)) if r["desc_genus"] else (None, "NO_NAME", "NONE", 0)

        a_sp, a_st, a_mt, a_cf = a
        b_sp, b_st, b_mt, b_cf = b
        weak = [n for n, c in ((inci, a_cf), (desc, b_cf)) if 0 < c < MIN_CONFIDENCE]

        ev = (f"GBIF {datetime.date.today().isoformat()}: "
              f"'{inci}' -> {a_sp or 'no match'} [{a_st}/{a_mt}/{a_cf}]; "
              f"'{desc}' -> {b_sp or 'no match'} [{b_st}/{b_mt}/{b_cf}]")

        if a_sp and b_sp and a_sp == b_sp and not weak:
            r["resolution"] = "gbif"
            r["resolved_to"] = a_sp
            r["resolution_note"] = f"Same taxon under two names; accepted name used. {ev}"
            resolved += 1
            mark = f"OK   -> {a_sp}"
        elif (a_sp and not b_sp) and not weak:
            r["resolution"] = "gbif"
            r["resolved_to"] = a_sp
            r["resolution_note"] = (
                f"Description name is not in the GBIF backbone; INCI name used. {ev}")
            resolved += 1
            mark = f"OK   -> {a_sp} (description name unknown to GBIF)"
        elif (b_sp and not a_sp) and not weak:
            r["resolution"] = "gbif"
            r["resolved_to"] = b_sp
            r["resolution_note"] = (
                f"INCI name is not in the GBIF backbone; description name used. {ev}")
            resolved += 1
            mark = f"OK   -> {b_sp} (INCI name unknown to GBIF)"
        else:
            r["resolution"] = "excluded"
            r["resolved_to"] = ""
            why = ("low-confidence match" if weak else
                   "two distinct accepted species" if a_sp and b_sp else
                   "neither name matched")
            r["resolution_note"] = f"EXCLUDED - {why}; GBIF cannot say which was intended. {ev}"
            excluded += 1
            mark = f"EXCL ({why})"

        print(f"  {r['ref_no']:>6} {inci:<30} vs {desc:<30} {mark}")

    gbif.save_cache(cache)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"\nresolved via GBIF : {resolved}")
    print(f"excluded          : {excluded}")
    print(f"cache             : {gbif.CACHE_PATH.name} ({len(cache)} names)")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as e:
        sys.exit(f"GBIF unreachable: {e}. Cached results in {gbif.CACHE_PATH} are still valid.")
