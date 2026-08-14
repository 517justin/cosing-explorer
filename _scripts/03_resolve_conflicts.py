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
import json
import sys
import time
import urllib.parse
import urllib.request

from common import CORRECTIONS, DATA

CACHE = DATA / "gbif_cache.json"
API = "https://api.gbif.org/v1/species/match?name={}"
MIN_CONFIDENCE = 90


def load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def lookup(name, cache):
    """GBIF backbone match for a binomial, cached."""
    if name in cache:
        return cache[name]
    url = API.format(urllib.parse.quote(name))
    req = urllib.request.Request(url, headers={"User-Agent": "cosing-kg/0.1"})
    with urllib.request.urlopen(req, timeout=30) as fh:
        data = json.load(fh)
    data["_retrieved_at"] = datetime.date.today().isoformat()
    cache[name] = data
    time.sleep(0.35)                      # be polite to a free public API
    return data


SPECIES_RANKS = {"SPECIES", "SUBSPECIES", "VARIETY", "FORM"}
# Biological-source rows cover plants, algae (Chromista) and fungi.
LIVING_KINGDOMS = {"Plantae", "Chromista", "Fungi", "Protozoa", "Bacteria"}


def accepted_species(rec):
    """Reduce a match to (accepted_species, status, matchType, confidence).

    A GBIF match on a synonym still reports the accepted species in `species`,
    so that field is the answer for both ACCEPTED and SYNONYM statuses.

    Three guards, all learned the hard way:
      - matchType HIGHERRANK means GBIF only got as far as a genus or family,
        which is not an answer to 'which species is this'.
      - a non-species rank is likewise not an answer.
      - without a kingdom check, 'Gutta percha' matches *Gutta* Wrase & Schmidt,
        a beetle. Animal matches for a botanical name are always wrong here.
    """
    if not rec or rec.get("matchType") in {"NONE", "HIGHERRANK"}:
        return None, "NO_MATCH", rec.get("matchType", "NONE") if rec else "NONE", 0
    conf = rec.get("confidence", 0)
    status = rec.get("status", "?")
    mtype = rec.get("matchType", "?")
    if rec.get("rank") not in SPECIES_RANKS:
        return None, f"RANK_{rec.get('rank')}", mtype, conf
    if rec.get("kingdom") not in LIVING_KINGDOMS:
        return None, f"KINGDOM_{rec.get('kingdom')}", mtype, conf
    return rec.get("species"), status, mtype, conf


def main():
    path = CORRECTIONS / "conflicts.csv"
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    cache = load_cache()

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

        a = accepted_species(lookup(inci, cache)) if r["inci_genus"] else (None, "NO_NAME", "NONE", 0)
        b = accepted_species(lookup(desc, cache)) if r["desc_genus"] else (None, "NO_NAME", "NONE", 0)

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

    CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False), encoding="utf-8")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"\nresolved via GBIF : {resolved}")
    print(f"excluded          : {excluded}")
    print(f"cache             : {CACHE} ({len(cache)} names)")


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as e:
        sys.exit(f"GBIF unreachable: {e}. Cached results in {CACHE} are still valid.")
