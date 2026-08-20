"""Normalise inventory_2026 into the same shape the Phase 1-3 pipeline expects.

The 2026 API uses different column names from the 2019 CSV (inciName vs
INCI name, chemicalDescription vs Chem/IUPAC Name / Description,
cosmeticRestriction vs Restriction). This maps them onto the schema 01_load.py
produces, so 02-06 can run unchanged against either source.

Fields the 2026 API adds -- status, sccsOpinion, maximumConcentration -- are
carried through; `update_date` has no equivalent and is left NULL.
"""

import re

from common import connect

CAS_TOKEN = re.compile(r"\d{2,7}-\d{2}-\d")
GENERIC = re.compile(r"\(\s*generic\s*\)", re.IGNORECASE)


def main():
    con = connect()
    rows = con.execute("""
        SELECT ref_no, "inciName", "innName", "phEurName", "casNo",
               "chemicalDescription", "cosmeticRestriction", "functionName",
               "status", "otherRestrictions", "maximumConcentration",
               "sccsOpinion"
        FROM inventory_2026 WHERE ref_no IS NOT NULL ORDER BY ref_no""").fetchall()

    out = []
    for (ref, inci, inn, pheur, cas, desc, restr, func, status,
         other, maxc, sccs) in rows:
        cleaned = GENERIC.sub(" ", cas or "")
        cleaned = re.sub(r"(\d)\s*-\s*(\d)", r"\1-\2", cleaned)
        nums = list(dict.fromkeys(CAS_TOKEN.findall(cleaned)))
        # The API joins repeated values with ' | '; the 2019 loader used commas.
        funcs = [f.strip() for f in (func or "").split("|") if f.strip()]
        out.append([
            ref, inci or "", inn or None, pheur or None, cas or None,
            nums, nums[0] if nums else None, bool(GENERIC.search(cas or "")),
            None, desc or None, restr or None, ", ".join(funcs) or None, funcs,
            None, None, status or None, other or None, maxc or None,
            sccs or None,
        ])

    con.execute("DROP TABLE IF EXISTS ingredient_v2026")
    con.execute("""
        CREATE TABLE ingredient_v2026 (
            ref_no INTEGER PRIMARY KEY, inci_name VARCHAR NOT NULL,
            inn_name VARCHAR, ph_eur_name VARCHAR, cas_raw VARCHAR,
            cas_numbers VARCHAR[], cas_primary VARCHAR, cas_is_generic BOOLEAN,
            cas_unparsed VARCHAR, description VARCHAR, restriction VARCHAR,
            function_raw VARCHAR, functions VARCHAR[], update_date_raw VARCHAR,
            update_date DATE, status VARCHAR, other_restrictions VARCHAR,
            max_concentration VARCHAR, sccs_opinion VARCHAR)""")
    con.executemany(
        f"INSERT INTO ingredient_v2026 VALUES ({','.join(['?'] * 19)})", out)

    n = con.execute("SELECT count(*) FROM ingredient_v2026").fetchone()[0]
    d = con.execute("SELECT count(*) FROM ingredient_v2026 "
                    "WHERE description IS NOT NULL").fetchone()[0]
    f = con.execute("SELECT count(*) FROM ingredient_v2026 "
                    "WHERE len(functions) > 0").fetchone()[0]
    r = con.execute("SELECT count(*) FROM ingredient_v2026 "
                    "WHERE restriction IS NOT NULL").fetchone()[0]
    print(f"ingredient_v2026 : {n}")
    print(f"  有敘述         : {d} ({d/n*100:.1f}%)")
    print(f"  有 Function    : {f} ({f/n*100:.1f}%)")
    print(f"  有法規限制     : {r}")
    con.close()


if __name__ == "__main__":
    main()
