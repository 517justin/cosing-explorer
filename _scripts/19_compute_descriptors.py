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

Reads SMILES from compound_v2026, writes descriptor columns back via
ALTER TABLE + UPDATE, following the pattern in 18_render_structures.py.

Usage:
    python _scripts/19_compute_descriptors.py [--limit N]
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Max compounds to process (0=all)")
    args = parser.parse_args()

    db = duckdb.connect(str(DB), read_only=True)
    query = "SELECT inchikey, smiles FROM compound_v2026 WHERE smiles IS NOT NULL"
    if args.limit:
        query += f" LIMIT {args.limit}"
    rows = db.execute(query).fetchall()
    db.close()
    print(f"Compounds with SMILES: {len(rows):,}")

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

    print(f"\nComputed={len(results):,}, Failed={fail:,}")

    db = duckdb.connect(str(DB))
    for col, sqltype in COLUMNS.items():
        try:
            db.execute(f"ALTER TABLE compound_v2026 ADD COLUMN {col} {sqltype}")
        except Exception:
            pass

    rows_out = [
        (d["logp"], d["tpsa"], d["hbd"], d["hba"], d["rotb"],
         d["rings"], d["arom"], d["heavy"], d["fsp3"], ik)
        for ik, d in results.items()
    ]
    db.executemany(
        f"""UPDATE compound_v2026 SET
            logp=?, tpsa=?, hbd=?, hba=?, rotb=?, rings=?, arom=?, heavy=?, fsp3=?
            WHERE inchikey=?""",
        rows_out,
    )
    n = db.execute("SELECT count(*) FROM compound_v2026 WHERE logp IS NOT NULL").fetchone()[0]
    db.close()
    print(f"Updated {n:,} compounds with descriptors in DB")


if __name__ == "__main__":
    main()
