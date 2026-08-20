#!/usr/bin/env bash
# Full pipeline. Idempotent: rebuilds kb.duckdb from the read-only CSV.
# Scripts are numbered in execution order.
#   01 load             format normalisation only
#   02 parse_taxon      dual-path family/genus/species parse -> conflicts.csv
#   03 resolve          settle conflicts against GBIF (network; cached)
#   04 clean_taxon      apply corrections -> `extract` table
#   05 gbif_taxonomy    full GBIF hierarchy + split families -> `taxon` table
#   06 parts            plant part / process / modifier vocabulary match
#   09 link_regulation  join the current Annex II-VI text (reads _data/cosing_2026/)
#   11 load_inventory    load the 2026 inventory beside the 2019 snapshot and compare
#   07 insights         cross-cutting analysis of what the data shows
#   00 profile          regenerate the profile report
#
# GBIF responses are cached in _data/gbif_cache.json, so a second run needs no
# network. Delete the cache to force a refresh (do this quarterly - APG moves).
#
# 08_fetch_annexes.py and 10_fetch_inventory.py are NOT run here: they re-download
# from the live EU database. Run them by hand to refresh _data/cosing_2026/.
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
$PY _scripts/01_load.py
$PY _scripts/02_parse_taxon.py
$PY _scripts/03_resolve_conflicts.py
$PY _scripts/04_clean_taxon.py
$PY _scripts/05_gbif_taxonomy.py
$PY _scripts/06_parts.py
$PY _scripts/09_link_regulation.py
$PY _scripts/11_load_inventory.py
$PY _scripts/07_insights.py
$PY _scripts/00_profile.py
