"""Shared paths and helpers for the COSING pipeline."""

import os
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


# ---------------------------------------------------------------- data source
# The pipeline can run against either the read-only 2019 CSV or the 2026
# inventory fetched from the live API. Set COSING_SOURCE=2026 to switch. The
# 2019 outputs keep their bare names so every existing report, acceptance check
# and git history stays valid; 2026 outputs are suffixed and sit alongside.
SOURCE = os.environ.get("COSING_SOURCE", "2019")
if SOURCE not in ("2019", "2026"):
    raise SystemExit(f"COSING_SOURCE must be 2019 or 2026, got {SOURCE!r}")
SUFFIX = "" if SOURCE == "2019" else "_v2026"


def T(base):
    """Table name for this run's source."""
    if base == "ingredient":
        return "ingredient" if SOURCE == "2019" else "ingredient_v2026"
    return base + SUFFIX


def conflicts_file():
    return "conflicts.csv" if SOURCE == "2019" else "conflicts_2026.csv"


def tag(text):
    """Suffix a report filename or title with the source when not 2019."""
    return text if SOURCE == "2019" else f"{text} ({SOURCE})"


def connect():
    import duckdb

    return duckdb.connect(str(DB))


def load_corrections(name):
    """Read a corrections CSV into a list of dicts."""
    import csv

    with open(CORRECTIONS / name, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))
