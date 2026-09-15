"""CosIng MCP Server — cosmetic ingredient knowledge base."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from cosing_mcp.data import CosIngData

mcp = MCPServer("cosing-mcp")
db = CosIngData()


@mcp.tool()
def lookup_ingredient(query: str) -> dict:
    """Look up a cosmetic ingredient by INCI name, CAS number, or CosIng ref number.

    Returns full details: description, functions, species, family, regulation, and Explorer link.
    """
    result = db.lookup(query)
    if not result:
        return {"error": f"No ingredient found for '{query}'"}
    return result


@mcp.tool()
def search_ingredients(
    query: str,
    function: str | None = None,
    family: str | None = None,
    restricted_only: bool = False,
    bio_only: bool = False,
    limit: int = 20,
) -> dict:
    """Search CosIng ingredients by keyword with optional filters.

    Args:
        query: Search term (matches INCI name, CAS, species, description)
        function: Filter by function (e.g. "SKIN CONDITIONING")
        family: Filter by botanical family (e.g. "Rosaceae")
        restricted_only: Only show ingredients with EU regulation restrictions
        bio_only: Only show plant/biological-source ingredients
        limit: Maximum results (default 20)
    """
    results = db.search(query, limit=limit, function=function, family=family,
                        restricted_only=restricted_only, bio_only=bio_only)
    return {"results": results, "count": len(results)}


@mcp.tool()
def get_species(name: str) -> dict:
    """Get information about a plant species and its cosmetic extracts.

    Args:
        name: Scientific name (e.g. "Lavandula angustifolia", "Rosa damascena")
    """
    result = db.get_species_info(name)
    if not result:
        return {"error": f"No species found for '{name}'"}
    return result


@mcp.tool()
def get_family(name: str) -> dict:
    """Get information about a botanical family — species count, top functions, restriction rate.

    Args:
        name: Family name (e.g. "Rosaceae", "Lamiaceae")
    """
    result = db.get_family_info(name)
    if not result:
        return {"error": f"No family found for '{name}'"}
    return result


@mcp.tool()
def get_regulation(ref_no: str) -> dict:
    """Get EU regulation details for a CosIng ingredient.

    Args:
        ref_no: CosIng reference number (e.g. "31464")
    """
    result = db.get_regulation(ref_no)
    if not result:
        return {"error": f"No ingredient found for ref_no '{ref_no}'"}
    return result


@mcp.tool()
def analyze_ingredient_list(ingredients: list[str]) -> dict:
    """Analyze a list of INCI names from a cosmetic product label.

    Matches each ingredient against the CosIng database and returns:
    - matched ingredients with functions, family, and regulation status
    - unmatched ingredients
    - summary statistics (bio-source count, restricted count, function/family distribution)

    Args:
        ingredients: List of INCI names (e.g. ["AQUA", "GLYCERIN", "ROSA DAMASCENA FLOWER WATER"])
    """
    return db.analyze_list(ingredients)


def main():
    db.load()
    mcp.run()


if __name__ == "__main__":
    main()
