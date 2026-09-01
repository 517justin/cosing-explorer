"""Build CosIng Ingredient Explorer static site from kb.duckdb.

Uses the full v2026 inventory (33,638 ingredients).
All ingredients are first-class citizens — bio-sourced and synthetic alike.

Outputs:
  docs/data/ingredients.json  – all ingredients with search/filter data
  docs/data/compounds.json    – compound details for molecular viewer
  docs/svg/{XX}.json          – gzip+base64 SVG chunks by InChIKey prefix

Run: .venv/bin/python _scripts/build_site.py
"""
import json, os, re, gzip, base64, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, '_data', 'kb.duckdb')
SVG_DIR = os.path.join(ROOT, '_data', 'structures')
OUT_DIR = os.path.join(ROOT, 'docs')

sys.path.insert(0, ROOT)
import duckdb

db = duckdb.connect(DB_PATH, read_only=True)

# ─── 1. Function index (sorted by count desc) ───
print("Building function index...")
fn_rows = db.execute('''
    SELECT fn, count(*) as cnt
    FROM ingredient_v2026, LATERAL unnest(functions) AS t(fn)
    WHERE fn IS NOT NULL
    GROUP BY 1 ORDER BY 2 DESC
''').fetchall()
fn_list = [r[0] for r in fn_rows]
fn_counts = [r[1] for r in fn_rows]
fn_idx = {name: i for i, name in enumerate(fn_list)}
print(f"  {len(fn_list)} functions")

# ─── 2. Family index (sorted by ingredient count desc) ───
print("Building family index...")
fam_rows = db.execute('''
    SELECT COALESCE(e.family_final, e.family_accepted) as fam,
           count(DISTINCT e.ref_no) as n,
           count(DISTINCT e.species_accepted) as sp
    FROM extract_v2026 e
    WHERE COALESCE(e.family_final, e.family_accepted) IS NOT NULL
    GROUP BY 1 ORDER BY 2 DESC
''').fetchall()
fam_list = [r[0] for r in fam_rows]
fam_counts = [r[1] for r in fam_rows]
fam_species = [r[2] for r in fam_rows]
fam_idx = {name: i for i, name in enumerate(fam_list)}
print(f"  {len(fam_list)} families")

# ─── 3. Compounds per species (top 8) ───
print("Loading compounds per species...")
cpd_rows = db.execute('''
    SELECT sc.species, sc.inchikey, c.formula, c.iupac_name
    FROM species_compounds_v2026 sc
    JOIN compound_v2026 c ON sc.inchikey = c.inchikey
    WHERE c.has_svg = true
    ORDER BY sc.species, c.formula
''').fetchall()
sp_cpds = defaultdict(list)
sp_cpd_count = defaultdict(int)
for sp, ik, formula, iupac in cpd_rows:
    sp_cpd_count[sp] += 1
    if len(sp_cpds[sp]) < 8:
        sp_cpds[sp].append([ik, formula, iupac or ''])
print(f"  {len(sp_cpd_count)} species with compounds")

# ─── 4. CAS → InChIKey mapping ───
print("Loading CAS→structure mapping...")
cas_ik = {}
cas_rows = db.execute('''
    SELECT cas, inchikey FROM cas_structure_v2026
    WHERE found = true AND inchikey IS NOT NULL
''').fetchall()
for cas, ik in cas_rows:
    cas_ik[cas] = ik
print(f"  {len(cas_ik)} CAS→InChIKey mappings")

# ─── 5. All ingredients ───
print("Loading all ingredients...")
rows = db.execute('''
    SELECT
        i.ref_no, i.inci_name, i.description, i.functions,
        i.cas_primary, i.status, i.restriction, i.other_restrictions,
        i.max_concentration,
        e.species_accepted, COALESCE(e.family_final, e.family_accepted) as fam,
        e.genus_gbif, e.order_name, e.kingdom,
        e.plant_part, e.process, e.gbif_key
    FROM ingredient_v2026 i
    LEFT JOIN extract_v2026 e ON i.ref_no = e.ref_no
    ORDER BY i.inci_name
''').fetchall()
print(f"  {len(rows)} rows")

# ─── 6. Build item objects ───
print("Building ingredient index...")
items = {}
bio_count = 0
restr_count = 0
struct_count = 0
order_list = []

for row in rows:
    (ref, name, desc, funcs, cas, status, restr, other_restr,
     max_conc, species, fam, genus, order, kingdom,
     parts, process, gbif_key) = row

    item = {
        'n': name or '',
        'f': [fn_idx[f] for f in (funcs or []) if f in fn_idx],
    }
    if status != 'Active':
        item['a'] = 0
    if desc:
        item['d'] = desc
    if cas:
        item['c'] = cas

    # Bio-sourced fields
    if species:
        bio_count += 1
        item['sp'] = species
        if fam and fam in fam_idx:
            item['fm'] = fam_idx[fam]
        if genus:
            item['g'] = genus
        if order:
            item['ord'] = order
        if kingdom:
            item['k'] = kingdom
        if parts:
            item['pt'] = parts
        if process:
            item['pr'] = process
        if gbif_key:
            item['gbif'] = gbif_key
        cc = sp_cpd_count.get(species, 0)
        if cc > 0:
            item['cc'] = cc
            item['tc'] = sp_cpds[species]

    # CAS-derived structure
    if cas and cas in cas_ik:
        item['ik'] = cas_ik[cas]
        struct_count += 1

    # Restrictions
    if restr:
        restr_count += 1
        item['re'] = restr
    if other_restr:
        item['or'] = other_restr
    if max_conc:
        item['mc'] = max_conc

    ref_str = str(ref)
    items[ref_str] = item
    order_list.append(ref_str)

print(f"  {len(items)} ingredients")
print(f"  {bio_count} bio-sourced, {restr_count} restricted, {struct_count} with CAS structure")

# ─── Write ingredients.json ───
os.makedirs(os.path.join(OUT_DIR, 'data'), exist_ok=True)
data = {
    'functions': fn_list,
    'fn_counts': fn_counts,
    'families': fam_list,
    'fam_counts': fam_counts,
    'fam_species': fam_species,
    'order': order_list,
    'items': items,
}
data_json = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
path = os.path.join(OUT_DIR, 'data', 'ingredients.json')
with open(path, 'w') as f:
    f.write(data_json)
size_mb = len(data_json) / 1024 / 1024
print(f"  ingredients.json: {size_mb:.2f} MB")

# ─── 7. Compound index (all with ≥2 species) ───
print("Building compound index...")
cpd_index_rows = db.execute('''
    WITH ranked AS (
        SELECT sc.inchikey,
               c.formula, c.iupac_name,
               count(DISTINCT sc.species) as sp_count
        FROM species_compounds_v2026 sc
        JOIN compound_v2026 c ON sc.inchikey = c.inchikey
        GROUP BY 1,2,3
        HAVING sp_count >= 2
        ORDER BY sp_count DESC
    )
    SELECT r.inchikey, r.formula, r.iupac_name, r.sp_count,
           sc.species, e.family_final
    FROM ranked r
    JOIN species_compounds_v2026 sc ON r.inchikey = sc.inchikey
    LEFT JOIN extract_v2026 e ON sc.species = e.species_accepted
    ORDER BY r.sp_count DESC, r.inchikey, sc.species
''').fetchall()

compounds = {}
for ik, formula, iupac, sp_count, sp, fam in cpd_index_rows:
    if ik not in compounds:
        compounds[ik] = {'f': formula, 'iupac': iupac or '', 'sp_map': {}}
    if sp and sp not in compounds[ik]['sp_map']:
        compounds[ik]['sp_map'][sp] = fam or ''

cpd_result = {}
for ik, d in compounds.items():
    sp_map = d['sp_map']
    fam_counts_local = {}
    for sp, fam in sp_map.items():
        if fam:
            fam_counts_local[fam] = fam_counts_local.get(fam, 0) + 1
    top_fams = sorted(fam_counts_local.items(), key=lambda x: -x[1])[:10]
    top_sp = sorted(sp_map.items(), key=lambda x: x[0])[:30]
    cpd_result[ik] = {
        'f': d['f'], 'iupac': d['iupac'],
        'n_sp': len(sp_map), 'n_fam': len(fam_counts_local),
        'top_fam': [[f, c] for f, c in top_fams],
        'top_sp': [[sp, fam] for sp, fam in top_sp],
    }

cpd_json = json.dumps(cpd_result, separators=(',', ':'), ensure_ascii=False)
cpd_path = os.path.join(OUT_DIR, 'data', 'compounds.json')
with open(cpd_path, 'w') as f:
    f.write(cpd_json)
print(f"  compounds.json: {len(cpd_json)/1024/1024:.2f} MB ({len(cpd_result)} compounds)")

db.close()

# ─── 8. SVG chunks ───
print("Building SVG chunks...")

def optimize_svg(raw):
    s = raw
    s = re.sub(r'<\?xml[^?]*\?>\n?', '', s)
    s = re.sub(r'<!--.*?-->', '', s, flags=re.DOTALL)
    for rm in [
        "xmlns:rdkit='http://www.rdkit.org/xml'",
        "xmlns:xlink='http://www.w3.org/1999/xlink'",
        "xml:space='preserve'",
        "version='1.1'",
        "baseProfile='full'",
    ]:
        s = s.replace(rm, '')
    s = re.sub(r" class='[^']*'", '', s)
    s = re.sub(
        r"style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:1\.5px;"
        r"stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1'",
        "style='fill:none;stroke:#000;stroke-width:1.5'", s)
    s = re.sub(
        r"style='fill:none;fill-rule:evenodd;stroke:#([0-9A-Fa-f]{6});stroke-width:1\.5px;"
        r"stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1'",
        r"style='fill:none;stroke:#\1;stroke-width:1.5'", s)
    s = re.sub(r"font-style:normal;font-weight:normal;", '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

svg_files = [f for f in os.listdir(SVG_DIR) if f.endswith('.svg')]
chunks = defaultdict(dict)
total_raw = 0
total_compressed = 0

for i, fname in enumerate(svg_files):
    ik = fname[:-4]
    prefix = ik[:2]
    path = os.path.join(SVG_DIR, fname)
    try:
        raw = open(path).read()
    except Exception:
        continue
    total_raw += len(raw)
    opt = optimize_svg(raw)
    gz = gzip.compress(opt.encode(), compresslevel=9)
    b64 = base64.b64encode(gz).decode('ascii')
    total_compressed += len(b64)
    chunks[prefix][ik] = b64

    if (i + 1) % 10000 == 0:
        print(f"  processed {i+1}/{len(svg_files)} SVGs...")

svg_out_dir = os.path.join(OUT_DIR, 'svg')
os.makedirs(svg_out_dir, exist_ok=True)
for prefix, data in chunks.items():
    chunk_path = os.path.join(svg_out_dir, f'{prefix}.json')
    with open(chunk_path, 'w') as f:
        json.dump(data, f, separators=(',', ':'))

print(f"  {len(svg_files)} SVGs -> {len(chunks)} chunks")
print(f"  Raw: {total_raw/1024/1024:.0f} MB -> Compressed: {total_compressed/1024/1024:.0f} MB")

# ─── Summary ───
total_site = 0
for dirpath, dirnames, filenames in os.walk(OUT_DIR):
    for f in filenames:
        total_site += os.path.getsize(os.path.join(dirpath, f))
print(f"\nTotal site size: {total_site/1024/1024:.1f} MB")
print("Done.")
