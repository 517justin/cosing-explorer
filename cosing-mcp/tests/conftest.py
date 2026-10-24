"""Shared fixtures for cosing-mcp tests."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from cosing_mcp.data import CosIngData

FIXTURES = Path(__file__).parent / "fixtures"


def _build_mini_data():
    """Build a minimal ingredients.json + compounds.json for testing."""
    items = {
        "87220": {
            "n": "ROSA DAMASCENA BUD EXTRACT",
            "f": [0],
            "d": "Rosa Damascena Bud Extract is the extract of the buds of Rosa damascena, Rosaceae",
            "c": "90106-38-0",
            "sp": "Rosa damascena",
            "fm": 0,
            "g": "Rosa",
            "ord": "Rosales",
            "k": "Plantae",
            "pt": ["bud"],
            "pr": "extract",
            "gbif": 3005382,
            "cc": 7,
        },
        "75528": {
            "n": "AQUA",
            "f": [1],
            "d": "Aqua is water",
            "c": "7732-18-5",
            "ik": "AQUAKEY-XXXXXX-N",
        },
        "34424": {
            "n": "GLYCERIN",
            "f": [0, 2],
            "d": "Glycerin is an organic compound",
            "c": "56-81-5",
            "ik": "TESTKEY-XXXXXX-N",
        },
        "31464": {
            "n": "1,2,4-BENZENETRIACETATE",
            "f": [3],
            "d": "1,2,4-Benzenetriacetate",
            "c": "613-03-6",
            "re": "II/1254",
        },
        "57058": {
            "n": "LAVANDULA ANGUSTIFOLIA FLOWER EXTRACT",
            "f": [0],
            "d": "Extract from the flowers of lavender, Lavandula angustifolia, Lamiaceae",
            "c": "84235-59-0",
            "sp": "Lavandula angustifolia",
            "fm": 1,
            "g": "Lavandula",
            "ord": "Lamiales",
            "k": "Plantae",
            "pt": ["flower"],
            "pr": "extract",
            "gbif": 2926959,
            "cc": 58,
        },
        "85721": {
            "n": "PHENOXYETHANOL",
            "f": [4],
            "d": "Phenoxyethanol is an organic compound",
            "c": "122-99-6",
            "re": "V/29",
        },
    }

    ingredients = {
        "functions": ["SKIN CONDITIONING", "SOLVENT", "SKIN CONDITIONING - HUMECTANT", "NOT REPORTED", "PRESERVATIVE"],
        "fn_counts": [2, 1, 1, 1, 1],
        "families": ["Rosaceae", "Lamiaceae"],
        "fam_counts": [1, 1],
        "fam_species": [["Rosa damascena"], ["Lavandula angustifolia"]],
        "order": list(items.keys()),
        "items": items,
        "sp_zh": {"Rosa damascena": "大馬士革玫瑰", "Lavandula angustifolia": "真正薰衣草"},
        "sp_en": {"Rosa damascena": "Damask rose", "Lavandula angustifolia": "English lavender"},
        "fam_zh": {"Rosaceae": "薔薇科", "Lamiaceae": "唇形科"},
        "fam_en": {"Rosaceae": "Rose family", "Lamiaceae": "Mint family"},
        "sp_ja": {"Rosa damascena": "ダマスクローズ"},
        "fam_ja": {"Rosaceae": "バラ科"},
    }

    compounds = {
        "TESTKEY-XXXXXX-N": {
            "f": "C10H16",
            "iupac": "test compound",
            "n_sp": 2,
            "n_fam": 1,
            "top_fam": [["Rosaceae", 1]],
            "top_sp": [["Rosa damascena", "Rosaceae"]],
            "nm": {"en": ["glycerol", "glycerin"], "zh": ["甘油"], "ja": ["グリセリン"]},
            "cid": 753,
            "mw": 92.09,
            "desc": [-1.76, 60.7, 3, 3, 1, 0, 0, 6, 1.0],
            "cr": [0, 1, 2],
        }
    }

    ingredient_compounds = {
        "AQUAKEY-XXXXXX-N": {"f": "H2O", "cid": 962, "mw": 18.015,
                             "nm": {"en": ["water"], "zh": ["純水"], "ja": ["精製水"]},
                             "desc": [-0.82, 9.2, 0, 1, 0, 0, 0, 1, 0.0]},
    }
    return ingredients, compounds, ingredient_compounds


# [ChEBI id, name, definition, category (0 biological, 1 chemical, 2 application), CosIng functions]
ROLES = {
    "chebi": {"data_version": "256"},
    "license": "CC BY 4.0",
    "roles": [
        [35469, "antidepressant", "A drug used for the treatment of depression.", 2, []],
        [22586, "antioxidant", "A substance that inhibits oxidation.", 1, ["ANTIOXIDANT", "SKIN CONDITIONING"]],
        [76924, "plant metabolite", "Any eukaryotic metabolite produced in plants.", 0, []],
    ],
}


SPECIES_COMPOUNDS = {
    "shared": {"Rosa damascena": [0]},
    "own_n": {"Rosa damascena": 4},
    "via": {"Rosa damascena": ["Rosa x damascena trigintipetala"]},
}


def mini_fetch():
    """Stand-in for cosing_mcp.data._fetch_json that serves the mini dataset."""
    ingredients, compounds, ingredient_compounds = _build_mini_data()
    files = {
        "ingredients.json": ingredients,
        "compounds.json": compounds,
        "ingredient_compounds.json": ingredient_compounds,
        "species_compounds.json": SPECIES_COMPOUNDS,
        "roles.json": ROLES,
    }
    return files.__getitem__


@pytest.fixture
def mini_db():
    """CosIngData loaded with minimal test data (no network)."""
    db = CosIngData()
    with patch("cosing_mcp.data._fetch_json", side_effect=mini_fetch()):
        db.load()
    return db
