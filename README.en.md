# Cosmetic Ingredient Explorer

**CosIng 化妝品成分探索器**

English | [繁體中文](README.md) | [日本語](README.ja.md)

An interactive knowledge graph and AI question answering for the 33,638 cosmetic ingredients in the EU CosIng database. You can browse families, species, functions, and compounds, ask questions in natural language, and analyze ingredient labels.

Live demo: [517justin.github.io/cosing-explorer](https://517justin.github.io/cosing-explorer/)

## Features

### Knowledge graph (Explorer)

- Full-database search: find any of the 33,638 ingredients by INCI name, CAS number, description, species, family, or common name (Chinese and English)
- Force-directed knowledge graph: a canvas-rendered graph you can pan, zoom, and click through
- Five node types: family, function, ingredient, species, and compound
- Ego-graph navigation: click any node to expand its neighborhood, and use the breadcrumb trail to go back
- Deep linking: URL parameters open a specific ingredient, family, species, function, compound, or search
- Compound structures: 62,139 molecular structure SVGs, loaded on demand and decompressed in the browser with DecompressionStream
- Molecular properties: the compound panel shows nine RDKit descriptors (LogP, TPSA, hydrogen-bond donors and acceptors, rotatable bonds, ring and aromatic ring counts, heavy atoms, Fsp3) and links straight to PubChem
- Compound Browser: a separate list of the 12,375 compounds reported from two or more species, with LogP and molecular weight range filters, formula and name search, sorting, and paging
- Evidence and sources: a compound page lists every species that reports it, most relevant first, each with the number of references LOTUS lists and a note on how many rest on a single reference. Species panels name LOTUS as the source, say when LOTUS has no data for a species (which does not mean it has no compounds), and name the other names, such as GBIF synonyms and varieties, through which compounds were credited
- Stereoisomers: a compound page links to the other compounds with the same planar structure (6,201 of the shared compounds have at least one)
- Species-specific compounds: the 49,764 compounds reported from only one species load on demand in the species and ingredient panels, 24 at a time, and each opens with its full details
- Species photos: loaded automatically from the GBIF Occurrence API
- Common names: Chinese names for 2,375 species and English names for 2,448, plus Chinese and English names for all 376 families, shown throughout the interface and searchable. Japanese names (和名) cover 1,587 species and 275 families
- Multilingual compound names: 6,815 compounds have English, Chinese, and Japanese names and aliases from Wikidata, so you can search for "caffeine", "槲皮素", or "ケルセチン"
- Trilingual UI: switch between Chinese, English, and Japanese with the language button. Labels and common names follow the selected language, and Japanese names (和名) are searchable, for example "ラベンダー"
- Filtering and sorting: filter by botanical source, restriction, structure, function, or family, and sort several ways
- Regulation data: Annexes II to VI of EU Cosmetics Regulation EC 1223/2009, shown in a structured, color-coded layout
- Dark mode: follows the system setting, or choose light or dark
- Fully static: no backend, deployed directly on GitHub Pages

### AI query layer (MCP server and skill)

- Natural-language queries: ask Claude Code questions such as "What are the functions of rose oil?" or "What's the CAS number of glycerin?"
- Ingredient label analysis: paste an ingredient list or a photo of one, and the skill identifies the INCI names and looks them all up
- Regulation lookup: check any ingredient's EU regulatory status (Annexes II to VI)
- Species and family info: taxonomy, extract lists, and compound counts; a species without LOTUS data is reported as such, not as having no compounds
- Chemical data: looking up an ingredient also returns the formula, PubChem link, and descriptors of its compound for all 7,281 ingredients that have a structure, plus multilingual names where Wikidata has them
- Explorer links: every result includes a deep link to the knowledge graph

## Graph node selection logic

Each node type's ego graph (the neighborhood expanded around a selected node) picks its neighbors by these rules:

### Family (center)

| Neighbor type | Selection logic | Max |
|---|---|---|
| Species | By ingredient count under this family | 30 |
| Functions | By usage count under this family | 15 |
| Ingredients | First ingredient from each of the top 15 species | 15 |
| Compounds | By species occurrence count | 20 |

### Function (center)

| Neighbor type | Selection logic | Max |
|---|---|---|
| Families | By ingredient count under this function | 35 |
| Ingredients | Sortable: Default / Regulated first / Botanical first | 15 |
| Compounds | By species occurrence count | 15 |

### Ingredient (center)

| Neighbor type | Selection logic | Max |
|---|---|---|
| Functions | All functions of this ingredient | All |
| Family | The ingredient's family | 1 |
| Species | The ingredient's source species | 1 |
| Related ingredients | Other ingredients from the same species | 15 |
| Compounds | By species occurrence count | 12 |

### Species (center)

| Neighbor type | Selection logic | Max |
|---|---|---|
| Functions | By usage count under this species | 10 |
| Compounds | By species occurrence count | 15 |

### Compound (center)

| Neighbor type | Selection logic | Max |
|---|---|---|
| Functions | By usage count across species containing this compound | 10 |
| Species | Species containing this compound | 20 |

## Deep linking

The Explorer supports URL parameters for direct navigation:

| Parameter | Example | Description |
|-----------|---------|-------------|
| `?ingredient=` | [`?ingredient=87220`](https://517justin.github.io/cosing-explorer/?ingredient=87220) | Open a specific ingredient's graph |
| `?family=` | [`?family=Rosaceae`](https://517justin.github.io/cosing-explorer/?family=Rosaceae) | Open a specific family's graph |
| `?species=` | [`?species=Rosa+damascena`](https://517justin.github.io/cosing-explorer/?species=Rosa+damascena) | Open a specific species' graph |
| `?function=` | [`?function=SKIN+CONDITIONING`](https://517justin.github.io/cosing-explorer/?function=SKIN+CONDITIONING) | Open a specific function's graph |
| `?compound=` | `?compound=CRPUJAZIXJMDBK-UHFFFAOYSA-N` | Open a specific compound's graph |
| `?search=` | [`?search=lavender`](https://517justin.github.io/cosing-explorer/?search=lavender) | Pre-fill search box and show results |
| `?lang=` | [`?lang=ja`](https://517justin.github.io/cosing-explorer/?lang=ja) | Set the UI language (`zh`, `en`, or `ja`). Works alongside other parameters and overrides the saved preference |

## AI queries (Claude Code)

### Installation

```bash
# 1. Install MCP Server
cd cosing-mcp && pip install -e .

# 2. Add to Claude Code
claude mcp add cosing-mcp -- cosing-mcp

# 3. Install the analysis skill (optional)
cp cosing-mcp/skill/cosing-analyze.md .claude/commands/
```

### Ingredient label analysis

Use the `/cosing-analyze` skill in Claude Code:

```
/cosing-analyze
AQUA, GLYCERIN, BUTYLENE GLYCOL, ROSA DAMASCENA FLOWER WATER,
PHENOXYETHANOL, CITRIC ACID, SODIUM HYALURONATE
```

You can also paste a photo of an ingredient label; the skill reads the INCI names from the image.

The report includes:
- Overview table (🌿 botanical / ⚗️ synthetic / 🔴 prohibited / 🟠 restricted / ✅ unrestricted)
- Botanical ingredients with species, common names, plant parts, and process
- Regulatory details (Annexes II to VI)
- Unmatched ingredients with possible reasons
- Function distribution
- Explorer graph links

### Natural-language Q&A

The MCP server provides six tools, and Claude picks the right one for each question:

| Tool | Description | Example question |
|------|-------------|-----------------|
| `lookup_ingredient` | Look up a single ingredient (INCI / CAS / ref_no) | "What is glycerin?" |
| `search_ingredients` | Fuzzy search with filters | "What lavender-related ingredients exist?" |
| `get_species` | Species details + extract list | "What extracts come from Rosa damascena?" |
| `get_family` | Family statistics | "How many ingredients are in Lamiaceae?" |
| `get_regulation` | Regulatory restriction query | "What are the restrictions on phenoxyethanol?" |
| `analyze_ingredient_list` | Batch ingredient analysis | Called by the `/cosing-analyze` skill |

## Data sources

| Data | Source | License |
|------|--------|---------|
| Cosmetic ingredients | [EU CosIng](https://data.europa.eu/data/datasets/cosing-list-ingredients-and-fragrance-inventory?locale=en) (European Commission) | Open Data |
| Taxonomy and synonyms | [GBIF](https://www.gbif.org/) Backbone Taxonomy | CC BY 4.0 |
| Compounds | [LOTUS](https://lotus.naturalproducts.net/) Natural Products | CC0 |
| Molecular structures | [PubChem](https://pubchem.ncbi.nlm.nih.gov/) | Public Domain |
| Multilingual names (compounds, species) and structures PubChem lacks | [Wikidata](https://www.wikidata.org/) | CC0 |

## Architecture

```
docs/                        # GitHub Pages root (Explorer)
├── index.html               # Single-page app (CSS/JS inlined, ~2,600 lines)
├── data/
│   ├── ingredients.json     # 33,638 ingredients + indexes + common names (~8 MB)
│   ├── compounds.json       # 12,375 compound index, compounds in 2+ species (~6 MB)
│   ├── species_compounds.json  # complete species -> compound lists, with reference counts (~0.7 MB)
│   └── ingredient_compounds.json  # 5,399 more compounds, for the MCP server (~0.8 MB)
├── own/                     # 49,764 species-specific compounds in 180 on-demand chunks (~11 MB)
└── svg/                     # 631 SVG chunks (~194 MB)
    └── add/                 # 619 chunks holding the 3,449 structures added later (~11 MB)

cosing-mcp/                  # AI query layer (MCP Server)
├── src/cosing_mcp/
│   ├── server.py            # MCP Server entry point + 6 tool definitions
│   └── data.py              # GitHub Pages JSON cache + in-memory indexes
├── tests/                   # 45 tests
├── skill/cosing-analyze.md  # Ingredient analysis skill (distributable copy)
└── pyproject.toml           # pip install config

.claude/
├── commands/cosing-analyze.md  # Claude Code Skill
└── settings.json               # MCP Server config

tests/explorer/              # Explorer UI and data tests (Node + jsdom, 36 tests)
requirements.txt             # Python dependencies for _scripts/
```

### SVG compression strategy

62,139 molecular structure SVGs are too many to inline into a single page, so the build compresses and chunks them:

1. Strip redundant XML declarations and styles
2. gzip compression (level 9)
3. Base64-encode into 631 JSON chunks
4. Browser-side decompression via the `DecompressionStream` API
5. Lazy loading: chunks are fetched and cached only when a user clicks a compound

## Local development

```bash
cd docs
python3 -m http.server 8765
```

Open `http://localhost:8765` in your browser.

## Rebuilding

To rebuild from source data:

```bash
# One-time setup
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# Requires _data/kb.duckdb and _data/structures/
.venv/bin/python _scripts/build_site.py              # rebuild all JSON and SVG chunks
.venv/bin/python _scripts/build_site.py --skip-svg   # JSON only (leaves docs/svg/ untouched)
.venv/bin/python _scripts/build_site.py --svg-new-only   # JSON plus structures not yet published
```

SVG chunks are written with a fixed gzip header, so repeated full builds are byte-identical. The chunks committed so far still carry build timestamps, so a full rebuild rewrites all 631 files once. Use `--svg-new-only` after adding compounds: it writes the structures that are not published yet to `docs/svg/add/`, which the Explorer reads when a main chunk has no entry, and leaves the 631 main chunks untouched (a full rebuild folds `svg/add/` back into them). Use `--skip-svg` otherwise.

To refresh the LOTUS join after a new LOTUS or GBIF release, run `13b_gbif_synonyms.py` (the GBIF synonyms of every species), `13_lotus.py`, `13c_check_synonyms.py` (asks GBIF what each synonym name really means, which drops homonyms such as `Annona glabra`) and `13_lotus.py` again. Without the check file no synonym is used.

When the LOTUS join finds new compounds (`COSING_SOURCE=2026 .venv/bin/python _scripts/13_lotus.py`), run `17_fetch_compound_smiles.py`, then `17b_wikidata_structures.py` (structures PubChem does not know, taken from Wikidata and checked against the InChIKey), then `17_fetch_compound_smiles.py` again to reload `compound_v2026`, `18_render_structures.py` and `19_compute_descriptors.py` before building.

To refresh multilingual names (queries Wikidata over SPARQL, about 20 minutes for a full run):

```bash
.venv/bin/python _scripts/20_fetch_wikidata_names.py species    # likewise families / compounds
.venv/bin/python _scripts/20b_merge_wikidata_names.py            # fill-only, never overwrites curated names
```

## Testing

```bash
cd cosing-mcp && pip install -e ".[dev]" && pytest       # MCP server, 45 tests
cd tests/explorer && npm install && npm test             # Explorer UI and data, 36 tests
```

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## Changelog

| Date | Description |
|------|-------------|
| 2026-10-21 | LOTUS problems 6 to 10: compounds LOTUS files under a GBIF synonym or a variety are now credited to the accepted species (42 more species have data, 4,158 more reports), but only after asking GBIF what each name means, because 637 of the 960 synonym names in LOTUS turned out to be accepted species in their own right (`Annona glabra` is not `Annona squamosa`). Compound pages list every reporting species, most relevant first, with reference counts and a note that 78% of reports rest on one reference; species panels name LOTUS, say when it has no data, and list the other names used; stereoisomers of one structure are linked. `get_species` says the same |
| 2026-10-19 | Recovered the compounds PubChem did not return: 1,768 of the 1,772 compounds that had dropped out of the pipeline now have structures from Wikidata (a SMILES is accepted only if the InChIKey recomputed from it matches the LOTUS key), and 400 records that came back without a SMILES were completed by CID. Shared compounds went from 11,810 to 11,978 and species-specific ones from 47,280 to 48,880; Zingiber officinale now lists 713 compounds, the number LOTUS reports. New structures go to an add-on layer, `svg/add/`, so the 631 main chunks stay untouched |
| 2026-10-18 | Hybrid species matched: LOTUS and Wikidata write hybrids with a multiplication sign (`Rosa × damascena`), so 5 species had lost their compounds (including the demo species Rosa damascena, now 75 compounds) and 16 their Wikidata names (for example Citrus limon, now レモン and 檸檬). Names are now compared without the sign. 94 new compounds were fetched and drawn, and `build_site.py --svg-new-only` adds structures without rewriting the other chunks |
| 2026-10-17 | Fixed three LOTUS display problems: the species-to-compound index was cut to 30 species per compound (22.7% of links lost, e.g. Vitis vinifera showed 222 of 352 shared compounds), ingredient panels listed compounds whose pages were empty (188 ingredients), and the 47,219 compounds reported from a single species were invisible. The Explorer now reads complete species lists, and species-specific compounds load on demand. `ingredients.json` shrank from 13 MB to 8 MB, and the MCP server counts a species' compounds from the complete index |
| 2026-10-15 | Names for the ingredient-only compounds: 3,355 of the 5,411 compounds in `ingredient_compounds.json` now carry English, Chinese, or Japanese names from Wikidata, and the MCP server searches them. Three species names that had been removed as invalid were refilled with real ones |
| 2026-10-05 | Tech debt cleared: the MCP server now has compound data for all 7,281 ingredients with a structure (it had 1,169), a `requirements.txt` for the build scripts, deterministic SVG chunking, an Explorer test suite (Node + jsdom, 18 tests), a toolbar fix for narrow windows, and five invalid common names removed. MCP tests went from 38 to 41 |
| 2026-10-02 | Phase 8b-i18n complete: Japanese UI in the Explorer (zh / EN / ja cycle, Japanese names shown and searchable, Japanese help, `?lang=` parameter), a Japanese-aware `cosing-analyze` skill, and a new `README.ja.md` |
| 2026-10-01 | Phase 8b complete: Wikidata multilingual names (en/zh/ja names and aliases for 6,581 compounds, Japanese names for 1,575 species and 275 families), name search, and Japanese names in the MCP server. Builds are now deterministic, and `build_site.py` has a `--skip-svg` flag. The species name gap shrank only partly (Chinese 519 to 457, English 464 to 379) because Wikidata has no common name for the rest |
| 2026-09-27 | Phase 8a complete: RDKit molecular descriptors, direct PubChem CID links, a Compound Browser with LogP and MW filters, and a descriptor field in the MCP server |
| 2026-09-27 | Phases 8b to 8d planned: Wikidata multilingual names, ChEBI chemical roles, COCONUT expansion, and a Japanese UI |
| 2026-09-15 | Phase 7 complete: an MCP server with six tools, Explorer deep links, the cosing-analyze skill, and 31 tests |

## License

[MIT License](LICENSE), Chia-Hsiu CHEN
