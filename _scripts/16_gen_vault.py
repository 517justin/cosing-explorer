#!/usr/bin/env python3
"""Phase 6: Generate Obsidian Vault notes from kb.duckdb (2026 inventory).

Outputs:
  10-Species/  ~2,827 species notes
  20-Family/   ~376 family notes
  30-MOC/      Function / Part / Process MOCs + index pages

Machine-generated content lives between <!-- AUTO-START --> and <!-- AUTO-END -->.
Everything after AUTO-END is human-authored and never touched by this script.
"""

import os, sys, textwrap
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent.parent
DB   = ROOT / "_data" / "kb.duckdb"

SPECIES_DIR  = ROOT / "10-Species"
FAMILY_DIR   = ROOT / "20-Family"
MOC_DIR      = ROOT / "30-MOC"

AUTO_START = "<!-- AUTO-START -->"
AUTO_END   = "<!-- AUTO-END -->"

# ── helpers ──────────────────────────────────────────────────────────────

def write_note(path: Path, frontmatter: str, auto_body: str, default_human: str = ""):
    """Write a note preserving any human content after AUTO-END."""
    human = default_human
    if path.exists():
        text = path.read_text(encoding="utf-8")
        idx = text.find(AUTO_END)
        if idx >= 0:
            human = text[idx + len(AUTO_END):]

    content = (
        f"---\n{frontmatter.strip()}\n---\n\n"
        f"{AUTO_START}\n\n{auto_body.strip()}\n\n{AUTO_END}"
        f"{human}"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def fmt(n):
    return f"{n:,}"


def safe_filename(name: str) -> str:
    return name.replace("/", "∕").replace("\\", "⧵").replace(":", "꞉")

# ── species notes ────────────────────────────────────────────────────────

def gen_species(db):
    print("Generating species notes …")

    species_info = db.execute("""
        SELECT species_accepted,
               any_value(genus_gbif)   AS genus,
               any_value(family_final) AS fam,
               any_value(order_name)   AS ord,
               any_value(kingdom)      AS kingdom,
               any_value(gbif_key)     AS gbif_key,
               count(DISTINCT ref_no)  AS n_extracts
        FROM extract_v2026
        WHERE species_accepted IS NOT NULL
        GROUP BY 1
    """).fetchall()

    parts_map = {}
    for sp, parts in db.execute("""
        SELECT species_accepted,
               array_agg(DISTINCT p ORDER BY p)
        FROM extract_v2026, unnest(plant_part) t(p)
        WHERE species_accepted IS NOT NULL AND p IS NOT NULL
        GROUP BY 1
    """).fetchall():
        parts_map[sp] = parts

    procs_map = {}
    for sp, procs in db.execute("""
        SELECT species_accepted,
               array_agg(DISTINCT process ORDER BY process)
        FROM extract_v2026
        WHERE species_accepted IS NOT NULL AND process IS NOT NULL
        GROUP BY 1
    """).fetchall():
        procs_map[sp] = procs

    funcs_map = {}
    for sp, funcs in db.execute("""
        SELECT e.species_accepted,
               array_agg(DISTINCT f ORDER BY f)
        FROM extract_v2026 e
        JOIN ingredient_v2026 i USING(ref_no),
             unnest(i.functions) t(f)
        WHERE e.species_accepted IS NOT NULL
        GROUP BY 1
    """).fetchall():
        funcs_map[sp] = funcs

    cpd_map = {}
    for sp, n in db.execute("""
        SELECT species, count(DISTINCT inchikey)
        FROM species_compounds_v2026
        GROUP BY 1
    """).fetchall():
        cpd_map[sp] = n

    restr_map = {}
    for sp, restriction in db.execute("""
        SELECT e.species_accepted, i.restriction
        FROM extract_v2026 e
        JOIN ingredient_v2026 i USING(ref_no)
        WHERE e.species_accepted IS NOT NULL AND i.restriction IS NOT NULL
    """).fetchall():
        restr_map.setdefault(sp, set()).add(restriction)

    inci_map = {}
    for sp, inci in db.execute("""
        SELECT e.species_accepted, i.inci_name
        FROM extract_v2026 e
        JOIN ingredient_v2026 i USING(ref_no)
        WHERE e.species_accepted IS NOT NULL
    """).fetchall():
        inci_map.setdefault(sp, set()).add(inci)

    n = 0
    for sp, genus, family, order, kingdom, gbif_key, n_ext in species_info:
        parts    = parts_map.get(sp, [])
        procs    = procs_map.get(sp, [])
        funcs    = funcs_map.get(sp, [])
        n_cpd    = cpd_map.get(sp, 0)
        restrs   = sorted(restr_map.get(sp, []))
        incis    = sorted(inci_map.get(sp, []))

        tags = ["species"]
        if family:
            tags.append(family)

        fm_lines = [
            f"accepted_name: \"{sp}\"",
            f"gbif_key: {gbif_key or ''}",
            f"genus: {genus or ''}",
            f"family: {family or ''}",
            f"order: {order or ''}",
            f"kingdom: {kingdom or ''}",
            f"extracts: {n_ext}",
            f"compounds: {n_cpd}",
            "tags:",
        ]
        for t in tags:
            fm_lines.append(f"  - {t}")

        body_parts = []

        # Taxonomy table
        body_parts.append("## Taxonomy\n")
        body_parts.append("| | |")
        body_parts.append("|---|---|")
        if family:
            body_parts.append(f"| Family | [[{family}]] |")
        if order:
            body_parts.append(f"| Order | {order} |")
        if kingdom:
            body_parts.append(f"| Kingdom | {kingdom} |")
        if gbif_key:
            body_parts.append(f"| GBIF | [{gbif_key}](https://www.gbif.org/species/{gbif_key}) |")

        # COSING extracts
        body_parts.append(f"\n## COSING Extracts\n")
        body_parts.append(f"{fmt(n_ext)} extract(s) in the 2026 inventory.\n")

        if incis:
            body_parts.append("**INCI names:**\n")
            for inci in incis[:20]:
                body_parts.append(f"- {inci}")
            if len(incis) > 20:
                body_parts.append(f"- … and {len(incis) - 20} more")

        if parts:
            body_parts.append(f"\n**Parts:** {', '.join(parts)}")

        if procs:
            body_parts.append(f"\n**Processes:** {', '.join(procs)}")

        # Functions
        if funcs:
            body_parts.append(f"\n## Functions\n")
            for f in funcs:
                fn = safe_filename(f)
                body_parts.append(f"- [[Function — {fn}|{f}]]")

        # Compounds
        if n_cpd:
            body_parts.append(f"\n## Compounds (LOTUS)\n")
            body_parts.append(f"{fmt(n_cpd)} distinct compounds (InChIKey).")

        # Regulation
        if restrs:
            body_parts.append(f"\n## Regulation\n")
            for r in restrs:
                body_parts.append(f"- Annex {r}")

        frontmatter = "\n".join(fm_lines)
        auto_body   = "\n".join(body_parts)

        fname = safe_filename(sp) + ".md"
        write_note(SPECIES_DIR / fname, frontmatter, auto_body,
                   default_human="\n\n## My Notes\n\n")
        n += 1

    print(f"  wrote {n} species notes")
    return n

# ── family notes ─────────────────────────────────────────────────────────

def gen_families(db):
    print("Generating family notes …")

    fam_info = db.execute("""
        SELECT family_final,
               any_value(order_name)   ord,
               any_value(kingdom)      kingdom,
               count(DISTINCT species_accepted) n_sp,
               count(DISTINCT ref_no)  n_ext
        FROM extract_v2026
        WHERE family_final IS NOT NULL
        GROUP BY 1
    """).fetchall()

    # Species per family with stats
    sp_per_fam = {}
    for fam, sp, n_ext, n_parts in db.execute("""
        SELECT e.family_final, e.species_accepted,
               count(DISTINCT e.ref_no),
               count(DISTINCT p)
        FROM extract_v2026 e
        LEFT JOIN unnest(e.plant_part) t(p) ON true
        WHERE e.family_final IS NOT NULL AND e.species_accepted IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """).fetchall():
        sp_per_fam.setdefault(fam, []).append((sp, n_ext, n_parts))

    # Compound counts per species (for family table)
    sp_cpd = {}
    for sp, n in db.execute("""
        SELECT species, count(DISTINCT inchikey)
        FROM species_compounds_v2026 GROUP BY 1
    """).fetchall():
        sp_cpd[sp] = n

    # Top functions per family
    fam_funcs = {}
    for fam, func, n_sp in db.execute("""
        SELECT e.family_final, f, count(DISTINCT e.species_accepted) n
        FROM extract_v2026 e
        JOIN ingredient_v2026 i USING(ref_no),
             unnest(i.functions) t(f)
        WHERE e.family_final IS NOT NULL AND e.species_accepted IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """).fetchall():
        fam_funcs.setdefault(fam, []).append((func, n_sp))

    # Restriction stats per family
    fam_restr = {}
    for fam, n_restr, n_total in db.execute("""
        SELECT e.family_final,
               count(*) FILTER (WHERE i.restriction IS NOT NULL),
               count(*)
        FROM extract_v2026 e
        JOIN ingredient_v2026 i USING(ref_no)
        WHERE e.family_final IS NOT NULL
        GROUP BY 1
    """).fetchall():
        fam_restr[fam] = (n_restr, n_total)

    # Annex breakdown per family (parse annex from restriction field)
    fam_annex = {}
    for fam, annex, n in db.execute("""
        SELECT e.family_final,
               split_part(i.restriction, '/', 1) AS annex,
               count(DISTINCT e.ref_no)
        FROM extract_v2026 e
        JOIN ingredient_v2026 i USING(ref_no)
        WHERE e.family_final IS NOT NULL AND i.restriction IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """).fetchall():
        fam_annex.setdefault(fam, []).append((annex, n))

    # Compound overview per family
    fam_cpd = {}
    for fam, n_cpd, n_sp in db.execute("""
        SELECT e.family_final,
               count(DISTINCT sc.inchikey),
               count(DISTINCT sc.species)
        FROM extract_v2026 e
        JOIN species_compounds_v2026 sc ON e.species_accepted = sc.species
        WHERE e.family_final IS NOT NULL
        GROUP BY 1
    """).fetchall():
        fam_cpd[fam] = (n_cpd, n_sp)

    n = 0
    for fam, order, kingdom, n_sp, n_ext in fam_info:
        restr_n, restr_total = fam_restr.get(fam, (0, n_ext))
        restr_pct = round(restr_n * 100 / restr_total, 1) if restr_total else 0
        cpd_n, cpd_sp = fam_cpd.get(fam, (0, 0))

        fm_lines = [
            f"family: {fam}",
            f"order: {order or ''}",
            f"kingdom: {kingdom or ''}",
            f"species_count: {n_sp}",
            f"extract_count: {n_ext}",
            f"compounds: {cpd_n}",
            "tags:",
            "  - family",
        ]

        body = []

        body.append("## Overview\n")
        body.append(f"- **{fmt(n_sp)}** species, **{fmt(n_ext)}** extracts")
        if restr_n > 0:
            body.append(f"- Restriction rate: {restr_pct}% ({restr_n} / {restr_total})")
        else:
            body.append(f"- No restrictions in current inventory")
        if cpd_n > 0:
            body.append(f"- **{fmt(cpd_n)}** distinct compounds (LOTUS), covering {cpd_sp} species")

        # Species table
        species = sp_per_fam.get(fam, [])
        body.append(f"\n## Species ({len(species)})\n")
        body.append("| Species | Extracts | Parts | Compounds |")
        body.append("|---|---|---|---|")
        for sp, sp_ext, sp_parts in species:
            cpd = sp_cpd.get(sp, 0)
            fn = safe_filename(sp)
            body.append(f"| [[{fn}]] | {sp_ext} | {sp_parts} | {cpd if cpd else '—'} |")

        # Top functions
        top_funcs = fam_funcs.get(fam, [])[:15]
        if top_funcs:
            body.append(f"\n## Top Functions\n")
            body.append("| Function | Species |")
            body.append("|---|---|")
            for func, fn_sp in top_funcs:
                fn = safe_filename(func)
                body.append(f"| [[Function — {fn}|{func}]] | {fn_sp} |")

        # Regulation
        if restr_n > 0:
            body.append(f"\n## Regulation\n")
            body.append(f"{restr_n} extract(s) restricted ({restr_pct}% of {restr_total}).\n")
            annexes = fam_annex.get(fam, [])
            for annex, ann_n in annexes:
                body.append(f"- Annex {annex}: {ann_n} entries")

        # Compounds
        if cpd_n > 0:
            body.append(f"\n## Compounds (LOTUS)\n")
            body.append(f"{fmt(cpd_n)} distinct compounds across {cpd_sp} species.")

        frontmatter = "\n".join(fm_lines)
        auto_body   = "\n".join(body)

        fname = safe_filename(fam) + ".md"
        write_note(FAMILY_DIR / fname, frontmatter, auto_body,
                   default_human="\n\n## My Notes\n\n")
        n += 1

    print(f"  wrote {n} family notes")
    return n

# ── MOC notes ────────────────────────────────────────────────────────────

def gen_moc_functions(db):
    print("Generating Function MOCs …")

    # Bio-source functions (have species/family)
    func_stats = db.execute("""
        SELECT f,
               count(DISTINCT e.species_accepted) n_sp,
               count(DISTINCT e.family_final)     n_fam,
               count(DISTINCT e.ref_no)            n_ext
        FROM extract_v2026 e
        JOIN ingredient_v2026 i USING(ref_no),
             unnest(i.functions) t(f)
        WHERE e.species_accepted IS NOT NULL AND e.family_final IS NOT NULL
        GROUP BY 1
    """).fetchall()

    # All functions (including non-bio-source)
    all_funcs = db.execute("""
        SELECT f, count(DISTINCT ref_no)
        FROM ingredient_v2026, unnest(functions) t(f)
        GROUP BY 1
    """).fetchall()
    bio_func_set = {r[0] for r in func_stats}
    non_bio = [(f, n) for f, n in all_funcs if f not in bio_func_set]

    # Top families per function
    func_fam = {}
    for f, fam, n_sp in db.execute("""
        SELECT f, e.family_final, count(DISTINCT e.species_accepted)
        FROM extract_v2026 e
        JOIN ingredient_v2026 i USING(ref_no),
             unnest(i.functions) t(f)
        WHERE e.species_accepted IS NOT NULL AND e.family_final IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """).fetchall():
        func_fam.setdefault(f, []).append((fam, n_sp))

    # Top species per function
    func_sp = {}
    for f, sp, n_ext in db.execute("""
        SELECT f, e.species_accepted, count(DISTINCT e.ref_no)
        FROM extract_v2026 e
        JOIN ingredient_v2026 i USING(ref_no),
             unnest(i.functions) t(f)
        WHERE e.species_accepted IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """).fetchall():
        func_sp.setdefault(f, []).append((sp, n_ext))

    n = 0
    for func, n_sp, n_fam, n_ext in func_stats:
        fm_lines = [
            f"type: function",
            f"function: \"{func}\"",
            f"species_count: {n_sp}",
            f"family_count: {n_fam}",
            "tags:",
            "  - MOC",
            "  - function",
        ]

        body = []
        body.append(f"## {func}\n")
        body.append(f"{fmt(n_sp)} species across {fmt(n_fam)} families ({fmt(n_ext)} extracts).\n")

        # Top families
        top_fam = func_fam.get(func, [])[:15]
        if top_fam:
            body.append("### Top Families\n")
            body.append("| Family | Species |")
            body.append("|---|---|")
            for fam, fam_sp in top_fam:
                body.append(f"| [[{fam}]] | {fam_sp} |")

        # Top species
        top_sp = func_sp.get(func, [])[:20]
        if top_sp:
            body.append("\n### Top Species\n")
            body.append("| Species | Extracts |")
            body.append("|---|---|")
            for sp, sp_ext in top_sp:
                fn = safe_filename(sp)
                body.append(f"| [[{fn}]] | {sp_ext} |")

        fname = safe_filename(func)
        write_note(MOC_DIR / f"Function — {fname}.md",
                   "\n".join(fm_lines), "\n".join(body),
                   default_human="\n\n## My Notes\n\n")
        n += 1

    for func, n_ingr in non_bio:
        fm_lines = [
            f"type: function",
            f"function: \"{func}\"",
            f"species_count: 0",
            f"family_count: 0",
            "tags:",
            "  - MOC",
            "  - function",
        ]
        body = [
            f"## {func}\n",
            f"No bio-source species. {fmt(n_ingr)} synthetic/non-bio ingredients carry this function.",
        ]
        fname = safe_filename(func)
        write_note(MOC_DIR / f"Function — {fname}.md",
                   "\n".join(fm_lines), "\n".join(body),
                   default_human="\n\n## My Notes\n\n")
        n += 1

    print(f"  wrote {n} Function MOCs ({len(non_bio)} non-bio stubs)")
    return n


def gen_moc_parts(db):
    print("Generating Part MOCs …")

    part_stats = db.execute("""
        SELECT p,
               count(DISTINCT e.species_accepted) n_sp,
               count(DISTINCT e.family_final) n_fam,
               count(DISTINCT e.ref_no) n_ext
        FROM extract_v2026 e, unnest(e.plant_part) t(p)
        WHERE e.species_accepted IS NOT NULL AND p IS NOT NULL
        GROUP BY 1
    """).fetchall()

    part_sp = {}
    for p, sp, n_ext in db.execute("""
        SELECT p, e.species_accepted, count(DISTINCT e.ref_no)
        FROM extract_v2026 e, unnest(e.plant_part) t(p)
        WHERE e.species_accepted IS NOT NULL AND p IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """).fetchall():
        part_sp.setdefault(p, []).append((sp, n_ext))

    part_fam = {}
    for p, fam, n_sp in db.execute("""
        SELECT p, e.family_final, count(DISTINCT e.species_accepted)
        FROM extract_v2026 e, unnest(e.plant_part) t(p)
        WHERE e.species_accepted IS NOT NULL AND e.family_final IS NOT NULL AND p IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """).fetchall():
        part_fam.setdefault(p, []).append((fam, n_sp))

    n = 0
    for part, n_sp, n_fam, n_ext in part_stats:
        fm_lines = [
            f"type: part",
            f"part: {part}",
            f"species_count: {n_sp}",
            "tags:",
            "  - MOC",
            "  - part",
        ]

        body = []
        body.append(f"## {part}\n")
        body.append(f"{fmt(n_sp)} species across {fmt(n_fam)} families ({fmt(n_ext)} extracts).\n")

        top_fam = part_fam.get(part, [])[:15]
        if top_fam:
            body.append("### Top Families\n")
            body.append("| Family | Species |")
            body.append("|---|---|")
            for fam, fam_sp in top_fam:
                body.append(f"| [[{fam}]] | {fam_sp} |")

        top_sp = part_sp.get(part, [])[:20]
        if top_sp:
            body.append("\n### Top Species\n")
            body.append("| Species | Extracts |")
            body.append("|---|---|")
            for sp, sp_ext in top_sp:
                fn = safe_filename(sp)
                body.append(f"| [[{fn}]] | {sp_ext} |")

        write_note(MOC_DIR / f"Part — {part}.md",
                   "\n".join(fm_lines), "\n".join(body),
                   default_human="\n\n## My Notes\n\n")
        n += 1

    print(f"  wrote {n} Part MOCs")
    return n


def gen_moc_processes(db):
    print("Generating Process MOCs …")

    proc_stats = db.execute("""
        SELECT process,
               count(DISTINCT species_accepted) n_sp,
               count(DISTINCT family_final) n_fam,
               count(DISTINCT ref_no) n_ext
        FROM extract_v2026
        WHERE species_accepted IS NOT NULL AND process IS NOT NULL
        GROUP BY 1
    """).fetchall()

    proc_sp = {}
    for pr, sp, n_ext in db.execute("""
        SELECT process, species_accepted, count(DISTINCT ref_no)
        FROM extract_v2026
        WHERE species_accepted IS NOT NULL AND process IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """).fetchall():
        proc_sp.setdefault(pr, []).append((sp, n_ext))

    proc_fam = {}
    for pr, fam, n_sp in db.execute("""
        SELECT process, family_final, count(DISTINCT species_accepted)
        FROM extract_v2026
        WHERE species_accepted IS NOT NULL AND family_final IS NOT NULL AND process IS NOT NULL
        GROUP BY 1, 2
        ORDER BY 1, 3 DESC
    """).fetchall():
        proc_fam.setdefault(pr, []).append((fam, n_sp))

    n = 0
    for proc, n_sp, n_fam, n_ext in proc_stats:
        fm_lines = [
            f"type: process",
            f"process: {proc}",
            f"species_count: {n_sp}",
            "tags:",
            "  - MOC",
            "  - process",
        ]

        body = []
        body.append(f"## {proc}\n")
        body.append(f"{fmt(n_sp)} species across {fmt(n_fam)} families ({fmt(n_ext)} extracts).\n")

        top_fam = proc_fam.get(proc, [])[:15]
        if top_fam:
            body.append("### Top Families\n")
            body.append("| Family | Species |")
            body.append("|---|---|")
            for fam, fam_sp in top_fam:
                body.append(f"| [[{fam}]] | {fam_sp} |")

        top_sp = proc_sp.get(proc, [])[:20]
        if top_sp:
            body.append("\n### Top Species\n")
            body.append("| Species | Extracts |")
            body.append("|---|---|")
            for sp, sp_ext in top_sp:
                fn = safe_filename(sp)
                body.append(f"| [[{fn}]] | {sp_ext} |")

        write_note(MOC_DIR / f"Process — {proc}.md",
                   "\n".join(fm_lines), "\n".join(body),
                   default_human="\n\n## My Notes\n\n")
        n += 1

    print(f"  wrote {n} Process MOCs")
    return n


def gen_moc_index(n_func, n_part, n_proc):
    """Generate index pages for each MOC category."""
    print("Generating MOC index pages …")

    # Functions index
    funcs_dir = MOC_DIR
    func_files = sorted(f.stem for f in funcs_dir.glob("Function — *.md"))
    body = ["## Function MOCs\n",
            f"{len(func_files)} functions.\n"]
    for f in func_files:
        body.append(f"- [[{f}]]")
    write_note(MOC_DIR / "Functions.md",
               "type: index\ntags:\n  - MOC\n  - index",
               "\n".join(body),
               default_human="\n")

    # Parts index
    part_files = sorted(f.stem for f in funcs_dir.glob("Part — *.md"))
    body = ["## Part MOCs\n",
            f"{len(part_files)} plant parts.\n"]
    for f in part_files:
        body.append(f"- [[{f}]]")
    write_note(MOC_DIR / "Parts.md",
               "type: index\ntags:\n  - MOC\n  - index",
               "\n".join(body),
               default_human="\n")

    # Processes index
    proc_files = sorted(f.stem for f in funcs_dir.glob("Process — *.md"))
    body = ["## Process MOCs\n",
            f"{len(proc_files)} processes.\n"]
    for f in proc_files:
        body.append(f"- [[{f}]]")
    write_note(MOC_DIR / "Processes.md",
               "type: index\ntags:\n  - MOC\n  - index",
               "\n".join(body),
               default_human="\n")

    print("  wrote 3 index pages")

# ── acceptance checks ────────────────────────────────────────────────────

def check(label, ok):
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {label}")
    return ok


def acceptance(db, n_sp, n_fam, n_func, n_part, n_proc):
    print("\n── Acceptance checks ──")

    db_sp  = db.execute("SELECT count(DISTINCT species_accepted) FROM extract_v2026 WHERE species_accepted IS NOT NULL").fetchone()[0]
    db_fam = db.execute("SELECT count(DISTINCT family_final) FROM extract_v2026 WHERE family_final IS NOT NULL").fetchone()[0]
    db_func = db.execute("SELECT count(DISTINCT f) FROM ingredient_v2026, unnest(functions) t(f)").fetchone()[0]
    db_part = db.execute("SELECT count(DISTINCT p) FROM extract_v2026, unnest(plant_part) t(p) WHERE p IS NOT NULL").fetchone()[0]
    db_proc = db.execute("SELECT count(DISTINCT process) FROM extract_v2026 WHERE process IS NOT NULL").fetchone()[0]

    ok = True
    ok &= check(f"species notes = {n_sp}, db has {db_sp}", n_sp == db_sp)
    ok &= check(f"family notes = {n_fam}, db has {db_fam}", n_fam == db_fam)
    ok &= check(f"Function MOCs = {n_func}, db has {db_func}", n_func == db_func)
    ok &= check(f"Part MOCs = {n_part}, db has {db_part}", n_part == db_part)
    ok &= check(f"Process MOCs = {n_proc}, db has {db_proc}", n_proc == db_proc)

    # Spot-check: every species note has AUTO markers
    sp_files = list(SPECIES_DIR.glob("*.md"))
    auto_ok = all(AUTO_START in f.read_text(encoding="utf-8") and AUTO_END in f.read_text(encoding="utf-8") for f in sp_files[:100])
    ok &= check(f"AUTO markers present in species notes (sample 100)", auto_ok)

    # Spot-check: every family note links to existing species notes
    broken = []
    for fam_file in FAMILY_DIR.glob("*.md"):
        text = fam_file.read_text(encoding="utf-8")
        for line in text.split("\n"):
            if "| [[" in line and "Function —" not in line:
                start = line.find("[[") + 2
                end   = line.find("]]", start)
                if start > 1 and end > start:
                    link = line[start:end].split("|")[0]
                    target = SPECIES_DIR / (link + ".md")
                    if not target.exists():
                        broken.append((fam_file.stem, link))
    ok &= check(f"broken wikilinks in family notes: {len(broken)}", len(broken) == 0)
    if broken:
        for fam, link in broken[:10]:
            print(f"    {fam} → {link}")

    # Check human section preserved
    ok &= check("index pages exist (Functions.md, Parts.md, Processes.md)",
                (MOC_DIR / "Functions.md").exists() and
                (MOC_DIR / "Parts.md").exists() and
                (MOC_DIR / "Processes.md").exists())

    if ok:
        print("\nAll acceptance checks passed ✓")
    else:
        print("\nSome checks FAILED")
        sys.exit(1)

# ── main ─────────────────────────────────────────────────────────────────

def main():
    db = duckdb.connect(str(DB), read_only=True)
    print(f"Phase 6: Vault generation from {DB.name}\n")

    n_sp   = gen_species(db)
    n_fam  = gen_families(db)
    n_func = gen_moc_functions(db)
    n_part = gen_moc_parts(db)
    n_proc = gen_moc_processes(db)
    gen_moc_index(n_func, n_part, n_proc)

    total = n_sp + n_fam + n_func + n_part + n_proc + 3
    print(f"\nTotal: {total} notes generated")

    acceptance(db, n_sp, n_fam, n_func, n_part, n_proc)


if __name__ == "__main__":
    main()
