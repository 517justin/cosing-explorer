#!/usr/bin/env bash
# Phase 1 pipeline. Idempotent: rebuilds kb.duckdb from the read-only CSV.
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
$PY _scripts/01_load.py
$PY _scripts/02_parse_taxon.py
$PY _scripts/03_clean_taxon.py
$PY _scripts/00_profile.py
