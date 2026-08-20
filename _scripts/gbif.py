"""Shared GBIF backbone lookup: on-disk cache, politeness, and match guards.

Both 03_resolve_conflicts.py and 05_gbif_taxonomy.py go through here so they
share one cache file and, more importantly, one definition of what counts as a
trustworthy match.
"""

import datetime
import json
import threading
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from common import DATA

CACHE_PATH = DATA / "gbif_cache.json"
API = "https://api.gbif.org/v1/species/match?name={}"

SPECIES_RANKS = {"SPECIES", "SUBSPECIES", "VARIETY", "FORM"}
# Biological-source rows cover plants, algae (Chromista) and fungi.
LIVING_KINGDOMS = {"Plantae", "Chromista", "Fungi", "Protozoa", "Bacteria"}

_lock = threading.Lock()


def load_cache():
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache, indent=1, ensure_ascii=False), encoding="utf-8")


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "cosing-kg/0.1"})
    with urllib.request.urlopen(req, timeout=30) as fh:
        return json.load(fh)


def _fetch(name):
    """Match a name, retrying with a kingdom hint if the backbone is ambiguous.

    GBIF returns matchType NONE with note 'Multiple equal matches' when its
    backbone holds duplicate entries for a name - 'Salix alba' is one, which is
    absurd to lose. Constraining the kingdom disambiguates it. The retry is
    only kept if it lands on a species-rank record in a plausible kingdom.
    """
    url = API.format(urllib.parse.quote(name))
    data = _get(url)
    if data.get("matchType") == "NONE":
        retry = _get(url + "&kingdom=Plantae")
        if retry.get("rank") in SPECIES_RANKS and retry.get("kingdom") in LIVING_KINGDOMS:
            retry["_kingdom_hint_used"] = True
            data = retry
    data["_retrieved_at"] = datetime.date.today().isoformat()
    return data


def lookup(name, cache):
    """Single cached match."""
    if name in cache:
        return cache[name]
    data = _fetch(name)
    with _lock:
        cache[name] = data
    return data


def lookup_many(names, cache, workers=4, progress=None):
    """Cached matches for many names, a few at a time.

    Four workers keeps this at roughly ten requests a second against a free
    public API - fast enough for a one-off backfill, gentle enough to be a good
    citizen. Anything already cached costs nothing.
    """
    missing = [n for n in dict.fromkeys(names) if n not in cache]
    if not missing:
        return cache
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for name, data in zip(missing, pool.map(_fetch, missing)):
            with _lock:
                cache[name] = data
            done += 1
            if progress and done % 100 == 0:
                progress(done, len(missing))
    if progress:
        progress(done, len(missing))
    return cache


def accepted(rec):
    """Reduce a match to a trustworthy result, or explain why there isn't one.

    Returns a dict with `ok` plus the backbone fields. Three guards:
      - matchType HIGHERRANK means GBIF only reached a genus or family, which
        is not an answer to 'which species is this'.
      - a non-species rank is likewise not an answer.
      - without a kingdom check, 'Gutta percha' matches *Gutta* Wrase &
        Schmidt, a beetle. An animal match for a botanical name is always wrong.
    """
    out = {
        "ok": False, "reason": "", "accepted_name": None, "gbif_key": None,
        "genus": None, "family": None, "order": None, "class": None,
        "phylum": None, "kingdom": None, "status": None, "match_type": None,
        "confidence": 0, "retrieved_at": (rec or {}).get("_retrieved_at"),
    }
    if not rec or rec.get("matchType") in {"NONE", "HIGHERRANK"}:
        out["reason"] = f"no_match:{(rec or {}).get('matchType', 'NONE')}"
        out["match_type"] = (rec or {}).get("matchType", "NONE")
        return out
    out.update(
        status=rec.get("status"), match_type=rec.get("matchType"),
        confidence=rec.get("confidence", 0),
    )
    if rec.get("rank") not in SPECIES_RANKS:
        out["reason"] = f"rank:{rec.get('rank')}"
        return out
    if rec.get("kingdom") not in LIVING_KINGDOMS:
        out["reason"] = f"kingdom:{rec.get('kingdom')}"
        return out
    out.update(
        ok=True, reason="",
        accepted_name=rec.get("species"),
        gbif_key=rec.get("acceptedUsageKey") or rec.get("usageKey"),
        genus=rec.get("genus"), family=rec.get("family"), order=rec.get("order"),
        **{"class": rec.get("class")},
        phylum=rec.get("phylum"), kingdom=rec.get("kingdom"),
    )
    return out
