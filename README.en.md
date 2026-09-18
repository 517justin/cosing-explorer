# Cosmetic Ingredient Explorer

**CosIng 化妝品成分探索器**

English | [繁體中文](README.md)

An interactive knowledge graph + AI Q&A for exploring 33,638 cosmetic ingredients in the EU CosIng database — families, species, functions, and compounds at a glance, plus natural-language queries and ingredient label analysis.

🔗 **[Live Demo → 517justin.github.io/cosing-explorer](https://517justin.github.io/cosing-explorer/)**

## Features

### Knowledge Graph (Explorer)

- **Full-database search** — Instant search across 33,638 ingredients (INCI name, CAS, description, species, family, common names in Chinese and English)
- **Force-directed knowledge graph** — Canvas-rendered interactive graph with pan, zoom, and click-to-navigate
- **Five node types** — Family, Function, Ingredient, Species, Compound
- **Ego-graph navigation** — Click any node to expand its neighborhood; breadcrumb trail for backtracking
- **Deep linking** — URL parameters to open specific ingredients, families, species, functions, compounds, or search results
- **Compound structures** — 58,596 molecular structure SVGs loaded on demand via DecompressionStream
- **Species photos** — Automatically loaded from the GBIF Occurrence API
- **Common names** — Chinese and English common names for 2,827 species and 376 families, searchable and displayed throughout
- **Bilingual UI** — Chinese / English toggle; all labels and common names switch with the language
- **Filtering & sorting** — Botanical / Restricted / Has structure / by Function / by Family filters, multiple sort modes
- **Regulation data** — EU Cosmetics Regulation EC 1223/2009 Annex II–VI with structured display and color coding
- **Dark mode** — Three-state theme (System / Light / Dark)
- **Fully static** — No backend; deployed directly on GitHub Pages

### AI Query Layer (MCP Server + Skill)

- **Natural-language queries** — Ask questions in Claude Code like "What are the functions of rose oil?" or "What's the CAS number of glycerin?"
- **Ingredient label analysis** — Paste ingredient list text or a photo to auto-identify INCI names and batch-query the database
- **Regulation lookup** — Instantly check any ingredient's EU regulatory status (Annex II–VI)
- **Species / Family info** — Query taxonomic details, extract lists, compound counts
- **Explorer links** — All query results include deep links to the knowledge graph for visual exploration

## Graph Node Selection Logic

Each node type's ego graph (the neighborhood expanded around a selected node) selects its neighbors according to the following rules:

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

## Deep Linking

The Explorer supports URL parameters for direct navigation:

| Parameter | Example | Description |
|-----------|---------|-------------|
| `?ingredient=` | [`?ingredient=87220`](https://517justin.github.io/cosing-explorer/?ingredient=87220) | Open a specific ingredient's graph |
| `?family=` | [`?family=Rosaceae`](https://517justin.github.io/cosing-explorer/?family=Rosaceae) | Open a specific family's graph |
| `?species=` | [`?species=Rosa+damascena`](https://517justin.github.io/cosing-explorer/?species=Rosa+damascena) | Open a specific species' graph |
| `?function=` | [`?function=SKIN+CONDITIONING`](https://517justin.github.io/cosing-explorer/?function=SKIN+CONDITIONING) | Open a specific function's graph |
| `?compound=` | `?compound=CRPUJAZIXJMDBK-UHFFFAOYSA-N` | Open a specific compound's graph |
| `?search=` | [`?search=lavender`](https://517justin.github.io/cosing-explorer/?search=lavender) | Pre-fill search box and show results |

## AI Queries (Claude Code)

### Installation

```bash
# 1. Install MCP Server
cd cosing-mcp && pip install -e .

# 2. Add to Claude Code
claude mcp add cosing-mcp -- cosing-mcp

# 3. Install the analysis skill (optional)
cp cosing-mcp/skill/cosing-analyze.md .claude/commands/
```

### Ingredient Label Analysis

Use the `/cosing-analyze` skill in Claude Code:

```
/cosing-analyze
AQUA, GLYCERIN, BUTYLENE GLYCOL, ROSA DAMASCENA FLOWER WATER,
PHENOXYETHANOL, CITRIC ACID, SODIUM HYALURONATE
```

You can also paste an ingredient label photo — the skill uses vision to identify INCI names.

The report includes:
- Overview table (🌿 botanical / ⚗️ synthetic / 🔴 prohibited / 🟠 restricted / ✅ unrestricted)
- Botanical ingredients with species, common names, plant parts, and process
- Regulatory details (Annex II–VI)
- Unmatched ingredients with possible reasons
- Function distribution
- Explorer graph links

### Natural-Language Q&A

The MCP Server provides 6 tools that Claude selects automatically:

| Tool | Description | Example question |
|------|-------------|-----------------|
| `lookup_ingredient` | Look up a single ingredient (INCI / CAS / ref_no) | "What is glycerin?" |
| `search_ingredients` | Fuzzy search with filters | "What lavender-related ingredients exist?" |
| `get_species` | Species details + extract list | "What extracts come from Rosa damascena?" |
| `get_family` | Family statistics | "How many ingredients are in Lamiaceae?" |
| `get_regulation` | Regulatory restriction query | "What are the restrictions on phenoxyethanol?" |
| `analyze_ingredient_list` | Batch ingredient analysis | Called by the `/cosing-analyze` skill |

## Data Sources

| Data | Source | License |
|------|--------|---------|
| Cosmetic ingredients | [EU CosIng](https://data.europa.eu/data/datasets/cosing-list-ingredients-and-fragrance-inventory?locale=en) (European Commission) | Open Data |
| Taxonomy | [GBIF](https://www.gbif.org/) Backbone Taxonomy | CC BY 4.0 |
| Compounds | [LOTUS](https://lotus.naturalproducts.net/) Natural Products | CC0 |
| Molecular structures | [PubChem](https://pubchem.ncbi.nlm.nih.gov/) | Public Domain |

## Architecture

```
docs/                        # GitHub Pages root (Explorer)
├── index.html               # Single-page app (CSS/JS inlined, ~2,000 lines)
├── data/
│   ├── ingredients.json     # 33,638 ingredients + indexes + common names (~13 MB)
│   └── compounds.json       # 11,777 compound index (~5 MB)
└── svg/                     # 631 SVG chunks (~192 MB)

cosing-mcp/                  # AI query layer (MCP Server)
├── src/cosing_mcp/
│   ├── server.py            # MCP Server entry point + 6 tool definitions
│   └── data.py              # GitHub Pages JSON cache + in-memory indexes
├── tests/                   # 31 tests
├── skill/cosing-analyze.md  # Ingredient analysis skill (distributable copy)
└── pyproject.toml           # pip install config

.claude/
├── commands/cosing-analyze.md  # Claude Code Skill
└── settings.json               # MCP Server config
```

### SVG Compression Strategy

58,596 molecular structure SVGs cannot be inlined into a single page. Solution:

1. Strip redundant XML declarations and styles
2. gzip compression (level 9)
3. Base64-encode into 631 JSON chunks
4. Browser-side decompression via the `DecompressionStream` API
5. Lazy loading — chunks are fetched and cached only when a user clicks on a compound

## Local Development

```bash
cd docs
python3 -m http.server 8765
```

Open `http://localhost:8765` in your browser.

## Rebuilding

To rebuild from source data:

```bash
# Requires _data/kb.duckdb and _data/structures/
python3 _scripts/build_site.py
```

## License

[MIT License](LICENSE) — Chia-Hsiu CHEN
