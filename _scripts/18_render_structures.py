#!/usr/bin/env python3
"""Render 2D structure SVGs from SMILES in compound_v2026.

Reads SMILES from compound_v2026, generates SVG with RDKit, stores them
in _data/structures/ as {inchikey}.svg. Skips files that already exist
(resume-safe). Also writes a summary table to compound_v2026.has_svg.

Usage:
    python _scripts/18_render_structures.py [--limit N] [--size 300]
"""
import argparse, sys
from pathlib import Path

import duckdb
from rdkit import Chem
from rdkit.Chem import Draw, AllChem, rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D

DB  = Path(__file__).resolve().parent.parent / "_data" / "kb.duckdb"
OUT = Path(__file__).resolve().parent.parent / "_data" / "structures"


def render_svg(smiles, size=300):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    try:
        rdDepictor.Compute2DCoords(mol)
    except Exception:
        return None

    drawer = rdMolDraw2D.MolDraw2DSVG(size, size)
    opts = drawer.drawOptions()
    opts.clearBackground = False
    opts.bondLineWidth = 1.5
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Max compounds to render (0=all)")
    parser.add_argument("--size", type=int, default=300, help="SVG width/height in px")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)

    db = duckdb.connect(str(DB), read_only=True)
    query = "SELECT inchikey, smiles FROM compound_v2026 WHERE smiles IS NOT NULL"
    if args.limit:
        query += f" LIMIT {args.limit}"
    rows = db.execute(query).fetchall()
    db.close()

    print(f"Compounds with SMILES: {len(rows):,}")

    existing = set(p.stem for p in OUT.glob("*.svg"))
    todo = [(ik, sm) for ik, sm in rows if ik not in existing]
    print(f"Already rendered: {len(existing):,}")
    print(f"To render: {len(todo):,}")

    ok = 0
    fail = 0
    for i, (ik, smiles) in enumerate(todo):
        svg = render_svg(smiles, args.size)
        if svg:
            (OUT / f"{ik}.svg").write_text(svg, "utf-8")
            ok += 1
        else:
            fail += 1

        if (i + 1) % 5000 == 0:
            print(f"  [{i+1}/{len(todo)}] ok={ok} fail={fail}")

    print(f"\nDone. Rendered={ok}, Failed={fail}")
    print(f"Total SVGs in {OUT}: {len(list(OUT.glob('*.svg'))):,}")

    # Update DB with has_svg flag
    db = duckdb.connect(str(DB))
    try:
        db.execute("ALTER TABLE compound_v2026 ADD COLUMN has_svg BOOLEAN DEFAULT FALSE")
    except Exception:
        pass
    svg_iks = [p.stem for p in OUT.glob("*.svg")]
    if svg_iks:
        db.execute("UPDATE compound_v2026 SET has_svg = FALSE")
        for batch_start in range(0, len(svg_iks), 1000):
            batch = svg_iks[batch_start:batch_start + 1000]
            placeholders = ",".join(f"'{ik}'" for ik in batch)
            db.execute(f"UPDATE compound_v2026 SET has_svg = TRUE WHERE inchikey IN ({placeholders})")
    n = db.execute("SELECT count(*) FROM compound_v2026 WHERE has_svg").fetchone()[0]
    db.close()
    print(f"Marked {n:,} compounds with has_svg=TRUE in DB")


if __name__ == "__main__":
    main()
