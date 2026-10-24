# cosing-mcp

MCP server for the [CosIng](https://single-market-economy.ec.europa.eu/sectors/cosmetics/cosmetic-ingredient-database_en) cosmetic ingredient knowledge base. It covers 33,638 ingredients, with botanical taxonomy, EU regulation status, and chemical compound data.

The data is hosted on [GitHub Pages](https://517justin.github.io/cosing-explorer/), so there is no backend to run. The server downloads it on first run and caches it locally.

## Install

```bash
pip install git+https://github.com/517justin/cosing-explorer.git#subdirectory=cosing-mcp
```

Or for development:

```bash
cd cosing-mcp
pip install -e .
```

## Add to Claude Code

```bash
claude mcp add cosing-mcp -- cosing-mcp
```

## Tools

| Tool | Description |
|------|-------------|
| `lookup_ingredient` | Look up by INCI name, CAS number, or ref number; returns the compound's ChEBI chemical roles and the CosIng functions they suggest |
| `search_ingredients` | Keyword search with filters (function, family, restricted, bio-source) |
| `get_species` | Species info: extracts, compounds, taxonomy |
| `get_family` | Family info: species count, top functions, restriction rate |
| `get_regulation` | EU regulation details (Annexes II to VI) |
| `analyze_ingredient_list` | Batch analyze a product's ingredient list |

### Examples

```
lookup_ingredient("ROSA DAMASCENA FLOWER WATER")
search_ingredients("lavender", bio_only=true)
get_species("Lavandula angustifolia")
get_family("Rosaceae")
get_regulation("31464")
analyze_ingredient_list(["AQUA", "GLYCERIN", "PHENOXYETHANOL"])
```

## Skill: ingredient label analysis

Copy the skill file to use `/cosing-analyze` in Claude Code:

```bash
cp cosing-mcp/skill/cosing-analyze.md .claude/commands/
```

Then provide a photo or text of a cosmetic ingredient label:

```
/cosing-analyze AQUA, GLYCERIN, BUTYLENE GLYCOL, ROSA DAMASCENA FLOWER WATER, PHENOXYETHANOL
```

## Data source

- `ingredients.json` (~8 MB): 33,638 CosIng ingredients with functions, taxonomy, and regulation
- `compounds.json` (~6 MB): 12,375 compounds linked to species
- `species_compounds.json` (~0.7 MB): the complete list of compounds per species, with reference counts and the other names compounds were credited through; used to count a species' compounds
- `ingredient_compounds.json` (~0.8 MB): structure data for 5,399 more compounds that belong to no species, so every ingredient with a structure returns its formula, PubChem link, and descriptors. 3,344 of them also carry English, Chinese, or Japanese names, and those names are searchable
- `roles.json` (~0.1 MB): 735 ChEBI chemical roles (CC BY 4.0) with the CosIng functions a hand-made table maps them to; optional, and `lookup_ingredient` leaves out `chemical_roles` and `suggested_cosing_functions` without it. The suggested functions are a guide, not what CosIng lists for the ingredient

Cached at `~/.cache/cosing-mcp/` with 7-day TTL. Works offline after first fetch.

## Explorer

Every tool response includes an `explorer_url` that links to the interactive [CosIng Explorer](https://517justin.github.io/cosing-explorer/) knowledge graph.
