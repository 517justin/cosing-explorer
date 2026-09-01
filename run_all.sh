#!/usr/bin/env bash
# Full pipeline. Idempotent: rebuilds the derived tables from source data.
#
# Two sources, selected with COSING_SOURCE (default 2019):
#   2019  the read-only COSING_CAS.csv snapshot -> ingredient, extract, taxon ...
#   2026  the inventory fetched from the live API -> *_v2026 tables
# Outputs never collide: 2019 keeps the bare names so every existing report and
# acceptance check stays valid, 2026 is suffixed and sits alongside.
#
#   ./run_all.sh          # 2019 snapshot
#   ./run_all.sh 2026     # current inventory
#
# 08_fetch_annexes.py and 10_fetch_inventory.py are NOT run here: they
# re-download from the live EU database. Run them by hand to refresh
# _data/cosing_2026/. GBIF and PubChem answers are cached (_data/gbif_cache.json,
# _data/pubchem_cache.json), so only the first run needs the network. LOTUS is
# read from _data/lotus/lotus_260413.csv.gz; re-download it from Zenodo to refresh.
set -euo pipefail
cd "$(dirname "$0")"
export COSING_SOURCE="${1:-${COSING_SOURCE:-2019}}"
PY=.venv/bin/python
echo "=== source: $COSING_SOURCE ==="

if [ "$COSING_SOURCE" = "2019" ]; then
  $PY _scripts/01_load.py                 # read the CSV
else
  $PY _scripts/11_load_inventory.py       # load + compare the 2026 inventory
  $PY _scripts/12_normalize_2026.py       # map it onto the pipeline's schema
fi

$PY _scripts/02_parse_taxon.py            # dual-path family/genus/species parse
$PY _scripts/03_resolve_conflicts.py      # settle conflicts against GBIF
$PY _scripts/04_clean_taxon.py            # apply corrections -> extract
$PY _scripts/05_gbif_taxonomy.py          # full GBIF hierarchy -> taxon
$PY _scripts/06_parts.py                  # plant part / process vocabulary
$PY _scripts/13_lotus.py                  # LOTUS species -> compounds
$PY _scripts/14_pubchem.py                # PubChem CAS -> structure (cached)
$PY _scripts/15_associations.py          # Phase 5: hidden associations
$PY _scripts/16_gen_vault.py             # Phase 6: vault notes

if [ "$COSING_SOURCE" = "2019" ]; then
  $PY _scripts/09_link_regulation.py      # current Annex II-VI text
  $PY _scripts/07_insights.py             # cross-cutting analysis
  $PY _scripts/00_profile.py              # profile report
fi
