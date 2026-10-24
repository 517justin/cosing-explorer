#!/usr/bin/env python3
"""Chemical roles from ChEBI for the project's compounds.

ChEBI (https://www.ebi.ac.uk/chebi, CC BY 4.0) is a chemical ontology in which a compound
can have roles ("antioxidant", "plant metabolite", "fragrance"): what the compound does or
is used for, which is the same question CosIng's function list answers for an ingredient.

  1. Parse _data/chebi/chebi.obo.gz (download it from
     https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.obo.gz).
  2. A role is any class below CHEBI:50906 "role". A compound has the roles it is given
     directly (relationship: RO:0000087 has role) and those of its is_a ancestors, because
     ChEBI states roles at the most general class that has them ("flavonols" are plant
     metabolites, so quercetin is).
  3. Match the project's compounds by InChIKey: exactly, or, for a key with stereochemistry
     that ChEBI knows only as a flat structure, by that structure (match 1).
  4. Write _data/chebi/compound_roles.json and _data/chebi/roles.json.

Role -> CosIng function mapping is curated by hand in _data/chebi/role_function.json
(see 21b_check_role_functions.py).

Usage:
    .venv/bin/python _scripts/21_load_chebi.py
"""
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
OBO = ROOT / "_data" / "chebi" / "chebi.obo.gz"
OUT_COMPOUNDS = ROOT / "_data" / "chebi" / "compound_roles.json"
OUT_ROLES = ROOT / "_data" / "chebi" / "roles.json"
DB = ROOT / "_data" / "kb.duckdb"

ROLE_ROOT = 50906  # CHEBI:50906 "role"
HAS_ROLE = "RO:0000087"
FLAT = "UHFFFAOYSA"  # stereo block of an InChIKey without stereochemistry
# the three classes directly below "role"; a role's category is the one it descends from
CATEGORIES = [(24432, "biological"), (51086, "chemical"), (33232, "application")]


def parse(path):
    """Stream the OBO file. Returns name, definition, is_a parents, direct roles, InChIKey, version."""
    name, definition, parents, roles, inchikey = {}, {}, defaultdict(list), defaultdict(list), {}
    version = {}
    cur = None
    obsolete = False
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line == "[Term]":
                cur, obsolete = None, False
                continue
            if line.startswith("["):
                cur = None
                continue
            if cur is None:
                if line.startswith("id: CHEBI:"):
                    cur = int(line[10:])
                elif line.startswith("data-version:"):
                    version["data_version"] = line.split(": ", 1)[1]
                elif line.startswith("date:"):
                    version["date"] = line.split(": ", 1)[1]
                continue
            if line.startswith("is_obsolete: true"):
                obsolete = True
                for d in (name, definition, inchikey):
                    d.pop(cur, None)
                parents.pop(cur, None)
                roles.pop(cur, None)
            elif obsolete:
                continue
            elif line.startswith("name: "):
                name[cur] = line[6:]
            elif line.startswith("def: "):
                m = re.match(r'def: "(.*?)" \[', line)
                if m:
                    definition[cur] = m.group(1)
            elif line.startswith("is_a: CHEBI:"):
                parents[cur].append(int(line[12:].split(" ", 1)[0]))
            elif line.startswith(f"relationship: {HAS_ROLE} CHEBI:"):
                roles[cur].append(int(line.split("CHEBI:", 1)[1].split(" ", 1)[0]))
            elif "inchi_key_string" in line:
                inchikey[cur] = line.split('"')[1]
    return name, definition, parents, roles, inchikey, version


def descendants(root, parents):
    children = defaultdict(list)
    for c, ps in parents.items():
        for p in ps:
            children[p].append(c)
    seen, stack = {root}, [root]
    while stack:
        for c in children[stack.pop()]:
            if c not in seen:
                seen.add(c)
                stack.append(c)
    return seen


def project_keys():
    con = duckdb.connect(str(DB), read_only=True)
    keys = {r[0] for r in con.execute("SELECT inchikey FROM compound_v2026").fetchall()}
    keys |= {r[0] for r in con.execute(
        "SELECT DISTINCT inchikey FROM cas_structure_v2026 WHERE found AND inchikey IS NOT NULL").fetchall()}
    con.close()
    return keys


def main():
    name, definition, parents, direct, inchikey, version = parse(OBO)
    role_ids = descendants(ROLE_ROOT, parents)
    print(f"ChEBI {version.get('data_version')} ({version.get('date')}): {len(name):,} terms, "
          f"{len(inchikey):,} with an InChIKey, {len(role_ids):,} role classes")

    memo = {}

    def inherited(cid):
        """Roles a class has: its own plus those of every is_a ancestor."""
        if cid in memo:
            return memo[cid]
        memo[cid] = got = set()  # guards against cycles
        got.update(r for r in direct.get(cid, ()) if r in role_ids)
        for p in parents.get(cid, ()):
            if p not in role_ids:
                got |= inherited(p)
        return got

    by_key = defaultdict(list)
    by_flat = defaultdict(list)
    for cid, key in inchikey.items():
        by_key[key].append(cid)
        if key.split("-")[1] == FLAT:
            by_flat[key.split("-")[0]].append(cid)

    compounds, exact, planar = {}, 0, 0
    keys = project_keys()
    for key in sorted(keys):
        ids, match = by_key.get(key), 0
        if not ids:
            ids, match = by_flat.get(key.split("-")[0]), 1
        if not ids:
            continue
        got = set()
        for cid in ids:
            got |= inherited(cid)
        if got:
            compounds[key] = [match, sorted(got)]
            exact += match == 0
            planar += match == 1

    used = {r for _, rs in compounds.values() for r in rs}
    # roles keep their role-ancestors so a role can be mapped through a more general one
    keep = set(used)
    stack = list(used)
    while stack:
        for p in parents.get(stack.pop(), ()):
            if p in role_ids and p not in keep:
                keep.add(p)
                stack.append(p)
    category_of = {}
    for index, (root, _label) in enumerate(CATEGORIES):
        for rid in descendants(root, parents):
            category_of.setdefault(rid, index)
    roles = {rid: [name[rid], definition.get(rid, ""), sorted(p for p in parents.get(rid, ()) if p in role_ids),
                   category_of.get(rid, len(CATEGORIES))]
             for rid in sorted(keep)}

    OUT_COMPOUNDS.write_text(json.dumps(
        {"chebi": version, "license": "CC BY 4.0", "source": "https://www.ebi.ac.uk/chebi",
         "compounds": compounds}, ensure_ascii=False, separators=(",", ":")), "utf-8")
    OUT_ROLES.write_text(json.dumps(roles, ensure_ascii=False, separators=(",", ":")), "utf-8")

    n_roles = Counter(r for _, rs in compounds.values() for r in rs)
    print(f"project compounds: {len(keys):,}; with roles: {len(compounds):,} "
          f"({exact:,} exact InChIKey, {planar:,} through the flat structure)")
    print(f"roles used: {len(used):,} (kept with ancestors: {len(keep):,}); "
          f"roles per compound: median {sorted(len(rs) for _, rs in compounds.values())[len(compounds) // 2]}")
    print("most common roles:")
    for rid, n in n_roles.most_common(15):
        print(f"  {n:6,}  CHEBI:{rid}  {name[rid]}  [{(CATEGORIES + [(0, 'other')])[roles[rid][3]][1]}]")
    print(f"wrote {OUT_COMPOUNDS.name} ({OUT_COMPOUNDS.stat().st_size / 1024:.0f} KB), "
          f"{OUT_ROLES.name} ({OUT_ROLES.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
