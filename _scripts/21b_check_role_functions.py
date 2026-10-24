#!/usr/bin/env python3
"""Validate the curated ChEBI role -> CosIng function mapping and measure how well it agrees.

The mapping lives in _data/chebi/role_function.json and is edited by hand. This script
checks that every role id exists in ChEBI with the name written next to it and that every
function is a real CosIng function, then compares the mapping with CosIng's own labels:
for each ingredient that has a structure, are the functions its compound's roles suggest
among the functions CosIng lists for it?

Usage:
    .venv/bin/python _scripts/21b_check_role_functions.py
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "_scripts"))

MAPPING = ROOT / "_data" / "chebi" / "role_function.json"
ROLES = ROOT / "_data" / "chebi" / "roles.json"
COMPOUNDS = ROOT / "_data" / "chebi" / "compound_roles.json"
INGREDIENTS = ROOT / "docs" / "data" / "ingredients.json"


def role_functions(mapping, roles):
    """role id -> functions, including those inherited from every more general role."""
    direct = {int(k): set(v["functions"]) for k, v in mapping["roles"].items()}
    memo = {}

    def up(rid):
        if rid not in memo:
            memo[rid] = got = set(direct.get(rid, ()))
            for p in roles[str(rid)][2]:
                got |= up(p)
        return memo[rid]

    return {int(rid): up(int(rid)) for rid in roles}


def main():
    mapping = json.loads(MAPPING.read_text("utf-8"))
    roles = json.loads(ROLES.read_text("utf-8"))
    compounds = json.loads(COMPOUNDS.read_text("utf-8"))["compounds"]
    ing = json.loads(INGREDIENTS.read_text("utf-8"))
    functions = set(ing["functions"])

    problems = []
    for rid, entry in mapping["roles"].items():
        if rid not in roles:
            problems.append(f"CHEBI:{rid} is not a role used by any project compound")
        elif roles[rid][0] != entry["role"]:
            problems.append(f"CHEBI:{rid} is '{roles[rid][0]}' in ChEBI, not '{entry['role']}'")
        for f in entry["functions"]:
            if f not in functions:
                problems.append(f"CHEBI:{rid}: '{f}' is not a CosIng function")
    if problems:
        sys.exit("\n".join(problems))

    mapped = role_functions(mapping, roles)
    covered = {f for fs in mapped.values() for f in fs}
    print(f"{len(mapping['roles'])} roles mapped to {len(covered)} of {len(functions)} CosIng functions")

    # compound -> functions its roles suggest
    suggested = {ik: set().union(*(mapped[r] for r in rs)) for ik, (_m, rs) in compounds.items()}
    suggested = {ik: fs for ik, fs in suggested.items() if fs}
    print(f"compounds with at least one suggested function: {len(suggested):,} of {len(compounds):,} with roles")

    # agreement with CosIng's labels, per function and overall
    seen = defaultdict(lambda: [0, 0])  # function -> [ingredients suggested, of which CosIng agrees]
    any_agree = n_ing = 0
    for it in ing["items"].values():
        fs = suggested.get(it.get("ik"))
        if not fs:
            continue
        own = {ing["functions"][i] for i in it["f"]}
        n_ing += 1
        any_agree += bool(fs & own)
        for f in fs:
            seen[f][0] += 1
            seen[f][1] += f in own
    print(f"ingredients with a structure and a suggested function: {n_ing:,}; "
          f"CosIng lists at least one of the suggested functions for {any_agree / n_ing:.0%}")
    print("\nfunction                          ingredients  CosIng agrees")
    for f, (n, ok) in sorted(seen.items(), key=lambda kv: -kv[1][0]):
        print(f"  {f:32s} {n:6,}      {ok / n:4.0%}")
    print("\nfunctions without a role:", ", ".join(sorted(functions - covered)[:12]), "...")


if __name__ == "__main__":
    main()
