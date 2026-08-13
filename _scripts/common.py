"""Shared paths and helpers for the COSING pipeline."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "_data"
CORRECTIONS = DATA / "corrections"
REPORTS = ROOT / "90-Reports"
RAW_CSV = DATA / "COSING_CAS.csv"
DB = DATA / "kb.duckdb"

# The eight conserved alternative family names, plus every -aceae token.
# Kept here because 01/02/03 all need the same definition of "looks like a family".
OLD_FAMILIES = [
    "Leguminosae",
    "Labiatae",
    "Compositae",
    "Umbelliferae",
    "Gramineae",
    "Guttiferae",
    "Palmae",
    "Cruciferae",
]

FAMILY_RE = r"(?:[A-Z][a-z]+aceae|" + "|".join(OLD_FAMILIES) + r")"


def connect():
    import duckdb

    return duckdb.connect(str(DB))


def load_corrections(name):
    """Read a corrections CSV into a list of dicts."""
    import csv

    with open(CORRECTIONS / name, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))
