#!/usr/bin/env bash
# Full pipeline. Idempotent: rebuilds kb.duckdb from the read-only CSV.
# Scripts are numbered in execution order.
#   01 load             format normalisation only
#   02 parse_taxon      dual-path family/genus/species parse -> conflicts.csv
#   03 resolve          settle conflicts against GBIF (network; cached)
#   04 clean_taxon      apply corrections -> `extract` table
#   05 gbif_taxonomy    full GBIF hierarchy + split families -> `taxon` table
#   00 profile          regenerate the profile report
#
# GBIF responses are cached in _data/gbif_cache.json, so a second run needs no
# network. Delete the cache to force a refresh (do this quarterly - APG moves).
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
$PY _scripts/01_load.py
$PY _scripts/02_parse_taxon.py
$PY _scripts/03_resolve_conflicts.py
$PY _scripts/04_clean_taxon.py
$PY _scripts/05_gbif_taxonomy.py
$PY _scripts/00_profile.py
