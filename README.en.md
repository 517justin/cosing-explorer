# Cosmetic Ingredient Explorer

**CosIng 化妝品成分探索器**

An interactive knowledge graph for visually exploring the relationships among 33,638 cosmetic ingredients in the EU CosIng database — families, species, functions, and compounds at a glance.

🔗 **[Live Demo → 517justin.github.io/cosing-explorer](https://517justin.github.io/cosing-explorer/)**

## Features

- **Full-database search** — Instant search across 33,638 ingredients (INCI name, CAS, description, species, family, common names in Chinese and English)
- **Force-directed knowledge graph** — Canvas-rendered interactive graph with pan, zoom, and click-to-navigate
- **Five node types** — Family, Function, Ingredient, Species, Compound
- **Ego-graph navigation** — Click any node to expand its neighborhood; breadcrumb trail for backtracking
- **Compound structures** — 58,596 molecular structure SVGs loaded on demand via DecompressionStream
- **Species photos** — Automatically loaded from the GBIF Occurrence API
- **Common names** — Chinese and English common names for 2,827 species and 376 families, searchable and displayed throughout
- **Bilingual UI** — Chinese / English toggle; all labels and common names switch with the language
- **Filter chips** — Botanical / Restricted / Has structure / by Function / by Family
- **Ingredient sorting** — Default, regulated-first, or botanical-first ordering
- **Ingredient detail panel** — Description, regulatory restrictions (color-coded Annex), taxonomic hierarchy, compound thumbnails
- **Regulation data** — EU Cosmetics Regulation EC 1223/2009 Annex II–VI with structured display and color coding
- **Dark mode** — Three-state theme (System / Light / Dark)
- **Fully static** — No backend; deployed directly on GitHub Pages

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

## Data Sources

| Data | Source | License |
|------|--------|---------|
| Cosmetic ingredients | [EU CosIng](https://data.europa.eu/data/datasets/cosing-list-ingredients-and-fragrance-inventory?locale=en) (European Commission) | Open Data |
| Taxonomy | [GBIF](https://www.gbif.org/) Backbone Taxonomy | CC BY 4.0 |
| Compounds | [LOTUS](https://lotus.naturalproducts.net/) Natural Products | CC0 |
| Molecular structures | [PubChem](https://pubchem.ncbi.nlm.nih.gov/) | Public Domain |

## Architecture

```
docs/                        # GitHub Pages root
├── index.html               # Single-page app (CSS/JS inlined, ~2,000 lines)
├── data/
│   ├── ingredients.json     # 33,638 ingredients + function index + family index + common names (~13 MB)
│   └── compounds.json       # 11,777 compound index (~5 MB)
└── svg/                     # 631 SVG chunks (bucketed by first two InChIKey chars, ~192 MB total)
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
