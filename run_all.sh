#!/usr/bin/env bash
# Phase 1 pipeline. Idempotent: rebuilds kb.duckdb from the read-only CSV.
# Scripts are numbered in execution order.
#   01 load            format normalisation only
#   02 parse_taxon     dual-path family/genus/species parse -> conflicts.csv
#   03 resolve         settle conflicts against GBIF (network; cached)
#   04 clean_taxon     apply corrections -> final `extract` table
#   00 profile         regenerate the profile report
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
$PY _scripts/01_load.py
$PY _scripts/02_parse_taxon.py
$PY _scripts/03_resolve_conflicts.py
$PY _scripts/04_clean_taxon.py
$PY _scripts/00_profile.py
