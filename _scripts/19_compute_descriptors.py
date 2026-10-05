#!/usr/bin/env python3
"""Compute RDKit molecular descriptors for compound_v2026.

Physical-property descriptors only (no classification/fingerprints):
  logp   - Crippen LogP (lipophilicity)
  tpsa   - Topological polar surface area
  hbd    - H-bond donors
  hba    - H-bond acceptors
  rotb   - Rotatable bonds
  rings  - Ring count
  arom   - Aromatic ring count
  heavy  - Heavy atom count
  fsp3   - Fraction of sp3 carbons

Reads SMILES from compound_v2026 (LOTUS compounds) and cas_structure_v2026
(compounds resolved from ingredient CAS numbers), writes descriptor columns back
via ALTER TABLE + UPDATE, following the pattern in 18_render_structures.py.

Usage:
    .venv/bin/python _scripts/19_compute_descriptors.py [--limit N]
"""
import argparse
from pathlib import Path

import duckdb
from rdkit import Chem
from rdkit.Chem import Crippen, Descriptors, Lipinski, rdMolDescriptors

DB = Path(__file__).resolve().parent.parent / "_data" / "kb.duckdb"

COLUMNS = {
    "logp":  "DOUBLE",
    "tpsa":  "DOUBLE",
    "hbd":   "INTEGER",
    "hba":   "INTEGER",
    "rotb":  "INTEGER",
    "rings": "INTEGER",
    "arom":  "INTEGER",
    "heavy": "INTEGER",
    "fsp3":  "DOUBLE",
}


def compute(smiles):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return {
        "logp":  round(Crippen.MolLogP(mol), 2),
        "tpsa":  round(rdMolDescriptors.CalcTPSA(mol), 1),
        "hbd":   Lipinski.NumHDonors(mol),
        "hba":   Lipinski.NumHAcceptors(mol),
        "rotb":  Lipinski.NumRotatableBonds(mol),
        "rings": rdMolDescriptors.CalcNumRings(mol),
        "arom":  rdMolDescriptors.CalcNumAromaticRings(mol),
        "heavy": mol.GetNumHeavyAtoms(),
        "fsp3":  round(rdMolDescriptors.CalcFractionCSP3(mol), 2),
    }


TABLES = [
    ("compound_v2026", "SELECT inchikey, smiles FROM compound_v2026 WHERE smiles IS NOT NULL"),
    ("cas_structure_v2026",
     "SELECT DISTINCT inchikey, smiles FROM cas_structure_v2026 "
     "WHERE found AND inchikey IS NOT NULL AND smiles IS NOT NULL ORDER BY inchikey, smiles"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Max compounds per table (0=all)")
    args = parser.parse_args()

    for table, query in TABLES:
        if args.limit:
            query += f" LIMIT {args.limit}"
        db = duckdb.connect(str(DB), read_only=True)
        rows = db.execute(query).fetchall()
        db.close()
        print(f"\n{table}: {len(rows):,} structures with SMILES")

        results = {}
        fail = 0
        for i, (ik, smiles) in enumerate(rows):
            d = compute(smiles)
            if d:
                results[ik] = d
            else:
                fail += 1
            if (i + 1) % 10000 == 0:
                print(f"  [{i+1}/{len(rows)}] computed={len(results)} fail={fail}")
        print(f"  computed={len(results):,}, failed={fail:,}")

        db = duckdb.connect(str(DB))
        for col, sqltype in COLUMNS.items():
            try:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {sqltype}")
            except Exception:
                pass

        rows_out = [
            (d["logp"], d["tpsa"], d["hbd"], d["hba"], d["rotb"],
             d["rings"], d["arom"], d["heavy"], d["fsp3"], ik)
            for ik, d in results.items()
        ]
        db.executemany(
            f"""UPDATE {table} SET
                logp=?, tpsa=?, hbd=?, hba=?, rotb=?, rings=?, arom=?, heavy=?, fsp3=?
                WHERE inchikey=?""",
            rows_out,
        )
        n = db.execute(f"SELECT count(*) FROM {table} WHERE logp IS NOT NULL").fetchone()[0]
        db.close()
        print(f"  updated {n:,} {table} rows with descriptors")


if __name__ == "__main__":
    main()
