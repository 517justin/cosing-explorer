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
- Compound structures: 58,596 molecular structure SVGs, loaded on demand and decompressed in the browser with DecompressionStream
- Species photos: loaded automatically from the GBIF Occurrence API
- Common names: Chinese and English common names for 2,827 species and 376 families, shown throughout the interface and searchable
- Multilingual compound names: 6,581 compounds have English, Chinese, and Japanese names and aliases from Wikidata, so you can search for "caffeine", "槲皮素", or "ケルセチン"
- Trilingual UI: switch between Chinese, English, and Japanese with the language button. Labels and common names follow the selected language, and Japanese names (和名) are searchable, for example "ラベンダー"
- Filtering and sorting: filter by botanical source, restriction, structure, function, or family, and sort several ways
- Regulation data: Annexes II to VI of EU Cosmetics Regulation EC 1223/2009, shown in a structured, color-coded layout
- Dark mode: follows the system setting, or choose light or dark
- Fully static: no backend, deployed directly on GitHub Pages

### AI query layer (MCP server and skill)

- Natural-language queries: ask Claude Code questions such as "What are the functions of rose oil?" or "What's the CAS number of glycerin?"
- Ingredient label analysis: paste an ingredient list or a photo of one, and the skill identifies the INCI names and looks them all up
- Regulation lookup: check any ingredient's EU regulatory status (Annexes II to VI)
- Species and family info: taxonomy, extract lists, and compound counts
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
| Taxonomy | [GBIF](https://www.gbif.org/) Backbone Taxonomy | CC BY 4.0 |
| Compounds | [LOTUS](https://lotus.naturalproducts.net/) Natural Products | CC0 |
| Molecular structures | [PubChem](https://pubchem.ncbi.nlm.nih.gov/) | Public Domain |
| Multilingual names (compounds, species) | [Wikidata](https://www.wikidata.org/) | CC0 |

## Architecture

```
docs/                        # GitHub Pages root (Explorer)
├── index.html               # Single-page app (CSS/JS inlined, ~2,000 lines)
├── data/
│   ├── ingredients.json     # 33,638 ingredients + indexes + common names (~13 MB)
│   └── compounds.json       # 11,777 compound index (~6 MB)
└── svg/                     # 631 SVG chunks (~192 MB)

cosing-mcp/                  # AI query layer (MCP Server)
├── src/cosing_mcp/
│   ├── server.py            # MCP Server entry point + 6 tool definitions
│   └── data.py              # GitHub Pages JSON cache + in-memory indexes
├── tests/                   # 38 tests
├── skill/cosing-analyze.md  # Ingredient analysis skill (distributable copy)
└── pyproject.toml           # pip install config

.claude/
├── commands/cosing-analyze.md  # Claude Code Skill
└── settings.json               # MCP Server config
```

### SVG compression strategy

58,596 molecular structure SVGs are too many to inline into a single page, so the build compresses and chunks them:

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
# Requires _data/kb.duckdb and _data/structures/
python3 _scripts/build_site.py              # rebuild all JSON and SVG chunks
python3 _scripts/build_site.py --skip-svg   # JSON only (leaves docs/svg/ untouched)
```

To refresh multilingual names (queries Wikidata over SPARQL, about 20 minutes for a full run; needs `duckdb` and `opencc-python-reimplemented`):

```bash
python3 _scripts/20_fetch_wikidata_names.py species    # likewise families / compounds
python3 _scripts/20b_merge_wikidata_names.py            # fill-only, never overwrites curated names
```

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## Changelog

| Date | Description |
|------|-------------|
| 2026-10-02 | Phase 8b-i18n complete: Japanese UI in the Explorer (zh / EN / ja cycle, Japanese names shown and searchable, Japanese help, `?lang=` parameter), a Japanese-aware `cosing-analyze` skill, and a new `README.ja.md` |
| 2026-10-01 | Phase 8b complete: Wikidata multilingual names (en/zh/ja names and aliases for 6,581 compounds, Japanese names for 1,575 species and 275 families), name search, and Japanese names in the MCP server. Builds are now deterministic, and `build_site.py` has a `--skip-svg` flag. The species name gap shrank only partly (Chinese 519 to 457, English 464 to 379) because Wikidata has no common name for the rest |
| 2026-09-27 | Phase 8a complete: RDKit molecular descriptors, direct PubChem CID links, a Compound Browser with LogP and MW filters, and a descriptor field in the MCP server |
| 2026-09-27 | Phases 8b to 8d planned: Wikidata multilingual names, ChEBI chemical roles, COCONUT expansion, and a Japanese UI |
| 2026-09-15 | Phase 7 complete: an MCP server with six tools, Explorer deep links, the cosing-analyze skill, and 31 tests |

## License

[MIT License](LICENSE), Chia-Hsiu CHEN
