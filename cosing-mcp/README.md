# cosing-mcp

MCP server for the [CosIng](https://single-market-economy.ec.europa.eu/sectors/cosmetics/cosmetic-ingredient-database_en) cosmetic ingredient knowledge base — 33,638 ingredients with botanical taxonomy, EU regulation status, and chemical compound data.

Data is served from [GitHub Pages](https://517justin.github.io/cosing-explorer/) (zero infrastructure). The server fetches and caches locally on first run.

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
| `get_species` | Species info — extracts, compounds, taxonomy |
| `get_family` | Family info — species count, top functions, restriction rate |
| `get_regulation` | EU regulation details (Annex II–VI) |
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

## Skill: Ingredient Label Analysis

Copy the skill file to use `/cosing-analyze` in Claude Code:

```bash
cp cosing-mcp/skill/cosing-analyze.md .claude/commands/
```

Then provide a photo or text of a cosmetic ingredient label:

```
/cosing-analyze AQUA, GLYCERIN, BUTYLENE GLYCOL, ROSA DAMASCENA FLOWER WATER, PHENOXYETHANOL
```

## Data Source

- **ingredients.json** (~13 MB) — 33,638 CosIng ingredients with functions, taxonomy, regulation
- **compounds.json** (~5 MB) — 11,777 compounds linked to species

Cached at `~/.cache/cosing-mcp/` with 7-day TTL. Works offline after first fetch.

## Explorer

All tool responses include an `explorer_url` linking to the interactive [CosIng Explorer](https://517justin.github.io/cosing-explorer/) knowledge graph.
