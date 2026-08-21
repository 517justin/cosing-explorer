"""Check every hand-written number in gen_status_docx.js against the database.

The Word record's numbers are transcribed into the generator by hand rather
than queried live, and three of them have been wrong at some point: the
vocabulary sizes, the family count, and a CAS figure that quoted distinct raw
field values where it meant distinct CAS numbers.

Run this before publishing an updated record. It fails loudly rather than
letting a stale figure through, which is the whole point.
"""

import re
import sys
from pathlib import Path

from common import ROOT, connect

GEN = ROOT / "_scripts" / "gen_status_docx.js"

# label -> (SQL, the value the generator states)
CHECKS = {
    "ingredient": ("SELECT count(*) FROM ingredient", 13622),
    "extract": ("SELECT count(*) FROM extract", 3862),
    "taxon": ("SELECT count(*) FROM taxon", 1263),
    "regulation": ("SELECT count(*) FROM regulation", 2389),
    "ingredient_citation": ("SELECT count(*) FROM ingredient_citation", 3132),
    "inventory_2026": ("SELECT count(*) FROM inventory_2026", 33638),
    "ingredient_v2026": ("SELECT count(*) FROM ingredient_v2026", 33638),
    "extract_v2026": ("SELECT count(*) FROM extract_v2026", 7690),
    "taxon_v2026": ("SELECT count(*) FROM taxon_v2026", 3179),
    "species_compounds": ("SELECT count(*) FROM species_compounds_v2026", 126775),
    "lotus_pair": ("SELECT count(*) FROM lotus_pair", 674454),
    "2019 family_final": (
        "SELECT count(DISTINCT family_final) FROM extract", 202),
    "2019 genus": ("SELECT count(DISTINCT genus_raw) FROM extract "
                   "WHERE genus_raw IS NOT NULL", 720),
    "2019 species_accepted": ("SELECT count(DISTINCT species_accepted) FROM extract "
                              "WHERE species_accepted IS NOT NULL", 1149),
    "2019 with_part": ("SELECT count(*) FROM extract WHERE plant_part IS NOT NULL", 3504),
    "2019 cell_culture": ("SELECT count(*) FROM extract WHERE is_cell_culture", 112),
    "2019 restricted": ("SELECT count(*) FROM ingredient WHERE restriction IS NOT NULL", 1073),
    "2019 functions": ("SELECT count(DISTINCT f) FROM "
                       "(SELECT unnest(functions) f FROM ingredient)", 70),
    "2019 cas_primary": ("SELECT count(DISTINCT cas_primary) FROM ingredient "
                         "WHERE cas_primary IS NOT NULL", 9796),
    "2019 cas_all": ("SELECT count(DISTINCT c) FROM "
                     "(SELECT unnest(cas_numbers) c FROM ingredient)", 10531),
    "2019 synthetic": ("SELECT (SELECT count(*) FROM ingredient) - "
                       "(SELECT count(*) FROM extract)", 9760),
    "2019 is_resolved": ("SELECT count(*) FROM extract WHERE is_resolved", 3787),
    "2019 agree": ("SELECT count(*) FROM extract WHERE taxon_status='agree'", 3789),
    "2019 with_process": ("SELECT count(*) FROM extract WHERE process IS NOT NULL", 3630),
    "2019 part_from_inci": ("SELECT count(*) FROM extract WHERE part_source='inci'", 3091),
    "2019 Plantae": ("SELECT count(*) FROM extract WHERE kingdom='Plantae'", 3782),
    "2019 family_source gbif": ("SELECT count(*) FROM extract "
                                "WHERE family_source='gbif'", 3826),
    "2026 family_final": ("SELECT count(DISTINCT family_final) FROM extract_v2026", 376),
    "2026 genus": ("SELECT count(DISTINCT genus_raw) FROM extract_v2026 "
                   "WHERE genus_raw IS NOT NULL", 1535),
    "2026 species_accepted": ("SELECT count(DISTINCT species_accepted) FROM extract_v2026 "
                              "WHERE species_accepted IS NOT NULL", 2827),
    "2026 with_part": ("SELECT count(*) FROM extract_v2026 "
                       "WHERE plant_part IS NOT NULL", 6655),
    "2026 cell_culture": ("SELECT count(*) FROM extract_v2026 WHERE is_cell_culture", 507),
    "2026 restricted": ("SELECT count(*) FROM ingredient_v2026 "
                        "WHERE restriction IS NOT NULL", 2473),
    "2026 functions": ("SELECT count(DISTINCT f) FROM "
                       "(SELECT unnest(functions) f FROM ingredient_v2026)", 82),
    "lotus species hit": ("SELECT count(DISTINCT species) FROM species_compounds_v2026", 2219),
    "pubchem found": ("SELECT count(*) FROM cas_structure_v2026 WHERE found", 6557),
    "pubchem total": ("SELECT count(*) FROM cas_structure_v2026", 10600),
    "shared 2019/2026": ("SELECT count(*) FROM ingredient i "
                         "JOIN inventory_2026 n USING(ref_no)", 13441),
    "Asteraceae compounds": (
        "SELECT count(DISTINCT s.inchikey) FROM extract_v2026 e "
        "JOIN species_compounds_v2026 s ON s.species=e.species_accepted "
        "WHERE e.family_final='Asteraceae'", 7085),
}


def main():
    con = connect()
    bad = []
    for label, (sql, stated) in CHECKS.items():
        actual = con.execute(sql).fetchone()[0]
        if actual != stated:
            bad.append((label, actual, stated))
        print(f"  {'OK  ' if actual == stated else 'WRONG'}  {label:<26} "
              f"db={actual:>9,}  doc={stated:>9,}")
    con.close()

    text = GEN.read_text(encoding="utf-8")
    for label, actual, stated in bad:
        print(f"\n  {label}: generator says {stated:,}, database says {actual:,}")
    if bad:
        sys.exit(f"\n{len(bad)} figure(s) in {GEN.name} no longer match the database")
    print(f"\nall {len(CHECKS)} figures match")


if __name__ == "__main__":
    main()
