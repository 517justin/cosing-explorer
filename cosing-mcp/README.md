# cosing-mcp

MCP server for the [CosIng](https://single-market-economy.ec.europa.eu/sectors/cosmetics/cosmetic-ingredient-database_en) cosmetic ingredient knowledge base. It covers 33,638 ingredients, with botanical taxonomy, EU regulation status, and chemical compound data.

The data is hosted on [GitHub Pages](https://517justin.github.io/cosing-explorer/), so there is no backend to run. The server downloads it on first run and caches it locally.

## Install

```bash
pip install git+https://github.com/517justin/cosing.git#subdirectory=cosing-mcp
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
| `lookup_ingredient` | Look up by INCI name, CAS number, or ref number |
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

- `ingredients.json` (~13 MB): 33,638 CosIng ingredients with functions, taxonomy, and regulation
- `compounds.json` (~5 MB): 11,777 compounds linked to species

Cached at `~/.cache/cosing-mcp/` with 7-day TTL. Works offline after first fetch.

## Explorer

Every tool response includes an `explorer_url` that links to the interactive [CosIng Explorer](https://517justin.github.io/cosing-explorer/) knowledge graph.
