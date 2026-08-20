"""Phase 1b - parse family / genus / species out of the biological-source rows.

Two independent paths, deliberately:

  A. INCI name        - 'PINUS PINASTER SEED OIL' -> Pinus pinaster
  B. Description text - '... of Pinus pinaster, Pinaceae.' -> Pinus pinaster + Pinaceae

The description is searched *anchored on the INCI genus* rather than by taking
the last binomial in the sentence. Taking the last binomial reads noise like
'Cape jasmine' or '(Locust bean)' as a species name; anchoring does not.

Where the two paths agree the row is accepted automatically. Where they disagree
the row is classified, and only genuine contradictions reach conflicts.csv for a
human decision - that disagreement is exactly how the typos in taxon_typo.csv
were found, so it is a feature rather than overhead.

NOTE ON ORDERING: the plan listed 02_clean before 03_parse_taxon. That order is
not executable - corrections apply to parsed tokens (family, genus), so parsing
has to come first. Scripts are numbered in true execution order instead.
"""

import csv
import re
from collections import Counter

from common import CORRECTIONS, FAMILY_RE, T, conflicts_file, connect

FAMILY_TOKEN = re.compile(r"\b" + FAMILY_RE + r"\b")
# The epithet may contain a hyphen (herba-alba) but must not end on one, so
# that 'Alisma plantago-aquatica' is not truncated to 'plantago-'.
BINOMIAL = re.compile(r"\b([A-Z][a-z]{2,})\s+([A-Za-z][a-z-]*[a-z])\b")

INCI_PREFIXES = {
    "HYDROLYZED", "HYDROGENATED", "OXIDIZED", "ACETYLATED", "SULFATED",
    "FERMENTED", "DEHYDRATED", "DISTILLED", "POTASSIUM", "SODIUM", "CALCIUM",
    "MAGNESIUM", "AMMONIUM", "ZINC",
    # Found by scanning the 2026 inventory for leading tokens ending in -ED /
    # -IZED that are not in the vocabulary: without these, 'DEFATTED NARCISSUS
    # TAZETTA FLOWER' parses its genus as "Defatted".
    "DEFATTED", "OZONIZED", "DEPOLYMERIZED", "CYCLIZED",
}

INCI_STOP = {
    "EXTRACT", "OIL", "WATER", "POWDER", "JUICE", "CERA", "WAX", "BUTTER",
    "LEAF", "ROOT", "SEED", "FLOWER", "FRUIT", "BARK", "STEM", "WOOD", "HERB",
    "BULB", "RHIZOME", "PEEL", "KERNEL", "SHOOT", "SPROUT", "TWIG", "BUD",
    "CALLUS", "GERM", "BRAN", "PULP", "CONE", "NUT", "THALLUS", "PIT", "SAP",
    "MERISTEM", "STALK", "PETAL", "POLLEN", "TUBER", "GUM", "RESIN", "LATEX",
    "HUSK", "SHELL", "WHOLE", "CULTURE", "FERMENT", "PROTEIN", "STARCH",
    "FLOUR", "MEAL", "FIBER", "LIPIDS", "ACID", "UNSAPONIFIABLES", "EXPRESSED",
    "ABSOLUTE", "CONCRETE", "TINCTURE", "GLYCERIDES", "OLEORESIN", "SEEDCAKE",
    "SPECIES", "HYBRID", "AND", "OF", "THE", "BALSAM", "GLYCOSIDE", "PEROXIDASE",
}

# Subset of INCI_STOP that can never be a genus. Plant-part words are excluded
# on purpose: TUBER, GUM and RESIN are all valid genus names somewhere.
PROCESS_STOP = {
    "EXTRACT", "OIL", "WATER", "POWDER", "JUICE", "CERA", "WAX", "BUTTER",
    "CULTURE", "FERMENT", "PROTEIN", "STARCH", "FLOUR", "MEAL", "FIBER",
    "LIPIDS", "ACID", "UNSAPONIFIABLES", "EXPRESSED", "ABSOLUTE", "CONCRETE",
    "TINCTURE", "GLYCERIDES", "OLEORESIN", "SEEDCAKE", "SPECIES", "HYBRID",
    "AND", "OF", "THE", "GLYCOSIDE", "PEROXIDASE", "WHOLE", "HYDROLYZED",
}

# Capitalised words that start a noun phrase in the description but are not
# genera. Only needed for the fallback path.
NOISE_GENUS = {
    "Cape", "Locust", "Balsam", "Fruit", "Seed", "Oil", "Butter", "Extract",
    "Powder", "Juice", "Water", "Syn", "Contains", "It", "The", "This", "St",
    "Bitter", "Sweet", "Common", "Wild", "White", "Black", "Red", "Green",
    "Holmboe", "Miller", "Linn", "Elder", "Gum", "Resin", "Root", "Leaf",
    "Flower", "Bark", "Wood", "Herb", "Whole", "Dried", "Fresh", "Protein",
    "Hydrolyzed", "Substance", "Product", "Obtained", "Derived", "Essential",
}


def levenshtein(a, b):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def inci_tokens(inci):
    toks = re.split(r"[\s/,]+", inci.upper())
    toks = [t.strip(".") for t in toks if t.strip(".")]
    while toks and toks[0] in INCI_PREFIXES:
        toks.pop(0)
    return toks


def _alpha(tok):
    """Alphabetic once hyphens are removed - epithets like herba-alba count."""
    return tok.replace("-", "").isalpha()


def parse_inci(inci):
    toks = inci_tokens(inci)
    if len(toks) < 2:
        return None, None, []
    genus, epithet = toks[0], toks[1]
    # The genus slot is only rejected for process words. Plant-part words are
    # allowed there because a few genera collide with them (TUBER MELANOSPORUM).
    if genus in PROCESS_STOP or epithet in INCI_STOP:
        return None, None, toks
    if not _alpha(genus) or not _alpha(epithet):
        return None, None, toks
    return genus.capitalize(), epithet.lower(), toks


# Synonyms the description volunteers about its own taxon. These are NOT
# alternative readings of the row - COSING is stating that two names denote the
# same plant - so they must not be mistaken for the row's binomial.
SYN_PAREN = re.compile(r"\(\s*syn[:.]?\s[^)]*\)", re.I)
SYN_CLAUSE = re.compile(r",?\s*syn[:.]\s.*$", re.I | re.S)


def description_candidates(desc):
    """(family, [(genus, epithet), ...]) - candidates ordered as they appear."""
    hits = list(FAMILY_TOKEN.finditer(desc))
    if not hits:
        return None, []
    last = hits[-1]
    # Strip synonyms only from the text before the family token, so the family
    # itself survives even when it follows a 'syn.' clause.
    head = SYN_CLAUSE.sub("", SYN_PAREN.sub(" ", desc[: last.start()]))
    cands = []
    for m in BINOMIAL.finditer(head):
        g, s = m.group(1), m.group(2).lower()
        if g in NOISE_GENUS or FAMILY_TOKEN.fullmatch(g):
            continue
        cands.append((g, s))
    return last.group(0), cands


def pick_candidate(cands, inci_genus):
    """Prefer the candidate whose genus matches the INCI genus.

    Scanned back-to-front. Many descriptions open by echoing the INCI name
    ('Phyllanthus Emblica Extract is an extract of the whole plant, Phyllanthus
    niruri, Euphorbiaceae') and that echo is sometimes the misspelled one. The
    binomial nearest the family token is the authoritative one.
    """
    if not cands:
        return None, None
    if inci_genus:
        for g, s in reversed(cands):
            if g == inci_genus:
                return g, s
        for g, s in reversed(cands):             # tolerate a genus typo
            if levenshtein(g.lower(), inci_genus.lower()) <= 2:
                return g, s
    return cands[-1]


def apply_typos(genus, species, typos, side):
    """Apply corrections registered for this side; return (g, s, applied).

    A correction's `side` is 'inci', 'description', or 'both' - 'both' is for
    names COSING misspells identically in the INCI name and the description,
    where the two paths agree with each other and are agreeing on an error.
    """
    applied = []
    for t in typos:
        if t["side"] not in (side, "both"):
            continue
        if t["scope_genus"] and t["scope_genus"] != genus:
            continue
        if t["rank"] == "genus" and genus == t["raw"]:
            genus = t["corrected"]
            applied.append(t["raw"])
        elif t["rank"] == "species" and species == t["raw"]:
            species = t["corrected"]
            applied.append(t["raw"])
    return genus, species, applied


def classify(inci, toks, ig, is_, dg, ds):
    """Why do the two paths disagree?"""
    up = inci.upper()
    if "SPECIES" in up or ds in {"spp", "species"}:
        return "genus_level_entry"
    if ig is None:
        # INCI is a trivial or trade name (COLOPHONIUM, FICIN, CANDELILLA CERA)
        # while the description still supplies a proper binomial.
        return "inci_not_binomial" if ds else "unparseable"
    if "HYBRID" in up or re.search(r"\bX\s+[A-Z]\.", up) or ds == "hybrida":
        return "hybrid"
    if ig == dg:
        # INCI splits a hyphenated epithet across two tokens: UVA URSI
        if len(toks) > 2 and f"{is_}-{toks[2].lower()}" == ds:
            return "hyphen_split"
        # INCI carries an infraspecific name the description spells out
        if ds and ds.upper() in toks:
            return "inci_truncated"
        # Distance 1 is a plausible slip. Distance 2 is not safe to assume:
        # bataua/bacaba are two different palms, not one misspelling.
        if levenshtein(is_, ds) == 1:
            return "spelling_variant"
        return "species_mismatch"
    if levenshtein(ig.lower(), dg.lower()) == 1:
        return "spelling_variant"
    return "genus_mismatch"


AUTO = {
    "genus_level_entry": "INCI names a genus rather than a species; genus kept, species left generic",
    "inci_not_binomial": "INCI is a trivial or trade name; binomial taken from the description",
    "hybrid": "Hybrid or multi-parent entry; description binomial kept as primary parent",
    "hyphen_split": "INCI splits a hyphenated epithet across two tokens; hyphenated form kept",
    "inci_truncated": "INCI truncates an infraspecific name; description form is more complete",
    "spelling_variant": "One side is misspelled (edit distance <= 2); INCI form kept, pair logged for review",
}
MANUAL = {"species_mismatch", "genus_mismatch", "unparseable"}


def main():
    con = connect()
    rows = con.execute(
        f"SELECT ref_no, inci_name, description FROM {T('ingredient')} "
        f"ORDER BY ref_no").fetchall()
    typos = _read("taxon_typo.csv")

    parsed, conflicts, spelling_log = [], [], []
    stats = Counter()

    for ref_no, inci, desc in rows:
        if not desc:
            continue
        family, cands = description_candidates(desc)
        if not family:
            continue                              # not a biological-source row
        stats["biological"] += 1

        ig, is_, toks = parse_inci(inci)
        ig, is_, ia = apply_typos(ig, is_, typos, "inci")
        dg, ds = pick_candidate(cands, ig)
        dg, ds, da = apply_typos(dg, ds, typos, "description")
        if ia or da:
            stats["typo_fixed"] += 1

        if ig is not None and (ig, is_) == (dg, ds):
            stats["agree"] += 1
            genus, species, src, kind = ig, is_, "both", "agree"
        elif dg is None:
            stats["desc_unparsed"] += 1
            genus, species, src, kind = ig, is_, "inci", "desc_unparsed"
        else:
            kind = classify(inci, toks, ig, is_, dg, ds)
            stats[f"conflict:{kind}"] += 1
            manual = kind in MANUAL
            # For a spelling variant the INCI spelling wins; otherwise the
            # description is the fuller record.
            if kind == "spelling_variant":
                genus, species, src = ig, is_, "inci"
                spelling_log.append((ref_no, inci, f"{ig} {is_}", f"{dg} {ds}"))
            elif kind == "genus_level_entry" and ig is None:
                genus, species, src = dg, ds, "description"
            else:
                genus, species, src = dg, ds, "description"
            conflicts.append(
                {
                    "ref_no": ref_no,
                    "inci_name": inci,
                    "inci_genus": ig or "",
                    "inci_species": is_ or "",
                    "desc_genus": dg or "",
                    "desc_species": ds or "",
                    "pattern": kind,
                    "resolution": "" if manual else "auto",
                    "resolved_to": "" if manual else f"{genus} {species}",
                    "resolution_note": "" if manual else AUTO[kind],
                }
            )
            if manual:
                genus, species, src = None, None, "unresolved"

        parsed.append(
            {
                "ref_no": ref_no,
                "family_raw": family,
                "genus_raw": genus,
                "species_raw": species,
                "binomial_raw": f"{genus} {species}" if genus and species else None,
                "taxon_source": src,
                "taxon_status": kind,
                "typo_applied": bool(ia or da),
            }
        )

    _write_table(con, parsed)
    _write_conflicts(conflicts)

    n = stats["biological"]
    manual_n = sum(1 for c in conflicts if not c["resolution"])
    print(f"biological-source rows : {n}")
    print(f"  both paths agree     : {stats['agree']} ({stats['agree']/n*100:.1f}%)")
    print(f"  token typos applied  : {stats['typo_fixed']}")
    print(f"  description unparsed : {stats['desc_unparsed']}")
    print(f"  auto-resolved        : {len(conflicts) - manual_n}")
    for k, v in sorted(stats.items()):
        if k.startswith("conflict:"):
            print(f"      {k[9:]:20} {v}")
    print(f"  NEED DECISION        : {manual_n} -> {conflicts_file()}")
    miss = con.execute(
        f"SELECT count(*) FROM {T('extract_parsed')} WHERE genus_raw IS NULL"
    ).fetchone()[0]
    print(f"  genus resolved       : {(1 - miss/n)*100:.2f}%  ({miss} unresolved)")
    if spelling_log:
        print(f"\n  spelling variants kept from INCI ({len(spelling_log)}):")
        for ref, _, a, b in spelling_log[:100]:
            print(f"      {ref:>6}  kept {a:<34} over {b}")
    con.close()


def _write_table(con, parsed):
    con.execute(f"DROP TABLE IF EXISTS {T('extract_parsed')}")
    con.execute(
        f"""
        CREATE TABLE {T('extract_parsed')} (
            ref_no        INTEGER PRIMARY KEY,
            family_raw    VARCHAR,
            genus_raw     VARCHAR,
            species_raw   VARCHAR,
            binomial_raw  VARCHAR,
            taxon_source  VARCHAR,
            taxon_status  VARCHAR,
            typo_applied  BOOLEAN
        )
        """
    )
    cols = list(parsed[0])
    con.executemany(
        f"INSERT INTO {T('extract_parsed')} VALUES "
        f"({','.join(['?'] * len(cols))})",
        [[p[c] for c in cols] for p in parsed],
    )


def _write_conflicts(conflicts):
    path = CORRECTIONS / conflicts_file()
    existing = {}
    if path.exists():                       # never clobber a human decision
        with open(path, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if r.get("resolution") and r["resolution"] != "auto":
                    existing[int(r["ref_no"])] = r
    for c in conflicts:
        old = existing.get(c["ref_no"])
        if old:
            c.update(
                resolution=old["resolution"],
                resolved_to=old["resolved_to"],
                resolution_note=old["resolution_note"],
            )
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(conflicts[0]))
        w.writeheader()
        w.writerows(conflicts)


def _read(name):
    with open(CORRECTIONS / name, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    main()
