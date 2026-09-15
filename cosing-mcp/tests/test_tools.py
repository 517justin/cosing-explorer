"""Tests for MCP tool wrappers."""

import asyncio
import json
from unittest.mock import patch

import pytest

from cosing_mcp.data import CosIngData
from cosing_mcp.server import mcp
from conftest import _build_mini_data


@pytest.fixture(autouse=True)
def _load_mini_db():
    """Replace the global db in server module with mini test data."""
    import cosing_mcp.server as srv
    ingredients, compounds = _build_mini_data()

    original_db = srv.db
    srv.db = CosIngData()
    with patch("cosing_mcp.data._fetch_json") as mock_fetch:
        def side_effect(name):
            if "ingredients" in name:
                return ingredients
            return compounds
        mock_fetch.side_effect = side_effect
        srv.db.load()
    yield
    srv.db = original_db


def _call(tool_name, args):
    result = asyncio.get_event_loop().run_until_complete(
        mcp.call_tool(tool_name, args)
    )
    return json.loads(result.content[0].text)


def test_lookup_ingredient():
    r = _call("lookup_ingredient", {"query": "87220"})
    assert r["inci_name"] == "ROSA DAMASCENA BUD EXTRACT"


def test_lookup_ingredient_not_found():
    r = _call("lookup_ingredient", {"query": "NONEXISTENT"})
    assert "error" in r


def test_search_ingredients():
    r = _call("search_ingredients", {"query": "rosa", "limit": 5})
    assert r["count"] >= 1
    assert len(r["results"]) <= 5


def test_search_ingredients_bio_only():
    r = _call("search_ingredients", {"query": "a", "bio_only": True})
    for item in r["results"]:
        assert "species" in item


def test_get_species():
    r = _call("get_species", {"name": "Rosa damascena"})
    assert r["species"] == "Rosa damascena"
    assert r["extract_count"] == 1


def test_get_species_not_found():
    r = _call("get_species", {"name": "Fake species"})
    assert "error" in r


def test_get_family():
    r = _call("get_family", {"name": "Rosaceae"})
    assert r["family"] == "Rosaceae"
    assert r["species_count"] >= 1


def test_get_family_not_found():
    r = _call("get_family", {"name": "Fakaceae"})
    assert "error" in r


def test_get_regulation():
    r = _call("get_regulation", {"ref_no": "31464"})
    assert r["restriction_text"] == "II/1254"


def test_get_regulation_not_found():
    r = _call("get_regulation", {"ref_no": "99999"})
    assert "error" in r


def test_analyze_ingredient_list():
    r = _call("analyze_ingredient_list", {
        "ingredients": ["AQUA", "GLYCERIN", "FAKE"]
    })
    assert r["summary"]["matched_count"] == 2
    assert r["summary"]["unmatched_count"] == 1
    assert "FAKE" in r["unmatched"]
