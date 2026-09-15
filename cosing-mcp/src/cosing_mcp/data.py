"""Fetch, cache, and index CosIng ingredient data from GitHub Pages."""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import quote

import httpx
from platformdirs import user_cache_dir

BASE_URL = "https://517justin.github.io/cosing-explorer/data/"
EXPLORER_URL = "https://517justin.github.io/cosing-explorer/"
CACHE_DIR = Path(user_cache_dir("cosing-mcp"))
MAX_AGE = 604800  # 7 days


def _cache_path(name: str) -> Path:
    return CACHE_DIR / name


def _is_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    return (time.time() - path.stat().st_mtime) < MAX_AGE


def _fetch_json(name: str) -> dict:
    """Fetch JSON from GitHub Pages, using local cache with 7-day TTL."""
    path = _cache_path(name)
    if _is_fresh(path):
        return json.loads(path.read_text("utf-8"))

    try:
        r = httpx.get(BASE_URL + name, timeout=60, follow_redirects=True)
        r.raise_for_status()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_bytes(r.content)
        return r.json()
    except (httpx.HTTPError, OSError):
        if path.exists():
            return json.loads(path.read_text("utf-8"))
        raise RuntimeError(
            f"Cannot fetch {name} and no local cache exists. "
            "Check your network connection."
        )


def explorer_url(param: str, value: str) -> str:
    return f"{EXPLORER_URL}?{param}={quote(value, safe='')}"


class CosIngData:
    """In-memory CosIng knowledge base with reverse indexes."""

    def __init__(self) -> None:
        self.items: dict[str, dict] = {}
        self.order: list[str] = []
        self.functions: list[str] = []
        self.families: list[str] = []
        self.compounds: dict[str, dict] = {}
        self.sp_zh: dict[str, str] = {}
        self.sp_en: dict[str, str] = {}
        self.fam_zh: dict[str, str] = {}
        self.fam_en: dict[str, str] = {}
        # reverse indexes
        self.by_inci: dict[str, str] = {}
        self.by_cas: dict[str, list[str]] = {}
        self.by_species: dict[str, list[str]] = {}
        self.by_family: dict[int, list[str]] = {}

    def load(self) -> None:
        ing = _fetch_json("ingredients.json")
        cpd = _fetch_json("compounds.json")

        self.items = ing["items"]
        self.order = ing["order"]
        self.functions = ing["functions"]
        self.families = ing["families"]
        self.compounds = cpd
        self.sp_zh = ing.get("sp_zh", {})
        self.sp_en = ing.get("sp_en", {})
        self.fam_zh = ing.get("fam_zh", {})
        self.fam_en = ing.get("fam_en", {})

        for ref, it in self.items.items():
            self.by_inci[it["n"].upper()] = ref
            if cas := it.get("c"):
                self.by_cas.setdefault(cas.strip(), []).append(ref)
            if sp := it.get("sp"):
                self.by_species.setdefault(sp, []).append(ref)
            if (fm := it.get("fm")) is not None:
                self.by_family.setdefault(fm, []).append(ref)

    def _format_item(self, ref: str) -> dict:
        it = self.items[ref]
        fn_names = [self.functions[i] for i in it.get("f", [])]
        result: dict = {
            "ref_no": ref,
            "inci_name": it["n"],
            "functions": fn_names,
            "explorer_url": explorer_url("ingredient", ref),
        }
        if d := it.get("d"):
            result["description"] = d
        if c := it.get("c"):
            result["cas"] = c
        if sp := it.get("sp"):
            result["species"] = sp
            if zh := self.sp_zh.get(sp):
                result["species_zh"] = zh
            if en := self.sp_en.get(sp):
                result["species_en"] = en
        if (fm := it.get("fm")) is not None:
            fam = self.families[fm]
            result["family"] = fam
            if zh := self.fam_zh.get(fam):
                result["family_zh"] = zh
            if en := self.fam_en.get(fam):
                result["family_en"] = en
        if k := it.get("k"):
            result["kingdom"] = k
        if pt := it.get("pt"):
            result["plant_parts"] = pt
        if pr := it.get("pr"):
            result["process"] = pr
        if re := it.get("re"):
            result["restriction"] = re
        if cc := it.get("cc"):
            result["compound_count"] = cc
        return result

    def lookup(self, query: str) -> dict | None:
        q = query.strip()
        if q in self.items:
            return self._format_item(q)
        if refs := self.by_cas.get(q):
            return self._format_item(refs[0])
        if ref := self.by_inci.get(q.upper()):
            return self._format_item(ref)
        return None

    def search(self, query: str, limit: int = 20,
               function: str | None = None, family: str | None = None,
               restricted_only: bool = False, bio_only: bool = False) -> list[dict]:
        q_upper = query.upper()
        results: list[tuple[int, str]] = []

        fn_idx = None
        if function:
            fn_upper = function.upper()
            for i, f in enumerate(self.functions):
                if f.upper() == fn_upper:
                    fn_idx = i
                    break

        fam_idx = None
        if family:
            for i, f in enumerate(self.families):
                if f.lower() == family.lower():
                    fam_idx = i
                    break

        for ref in self.order:
            it = self.items[ref]
            if fn_idx is not None and fn_idx not in it.get("f", []):
                continue
            if fam_idx is not None and it.get("fm") != fam_idx:
                continue
            if restricted_only and not it.get("re"):
                continue
            if bio_only and not it.get("sp"):
                continue

            name_upper = it["n"].upper()
            score = 0
            if name_upper == q_upper:
                score = 3
            elif q_upper in name_upper:
                score = 2
            else:
                cas = (it.get("c") or "").upper()
                sp = (it.get("sp") or "").upper()
                desc = (it.get("d") or "").upper()
                sp_zh = self.sp_zh.get(it.get("sp", ""), "").upper()
                sp_en = self.sp_en.get(it.get("sp", ""), "").upper()
                if q_upper in cas or q_upper in sp or q_upper in sp_zh or q_upper in sp_en:
                    score = 1
                elif q_upper in desc:
                    score = 1

            if score > 0:
                results.append((score, ref))

            if len(results) >= limit * 5:
                break

        results.sort(key=lambda x: -x[0])
        return [self._format_item(ref) for _, ref in results[:limit]]

    def get_species_info(self, name: str) -> dict | None:
        refs = self.by_species.get(name)
        if not refs:
            return None

        first = self.items[refs[0]]
        result: dict = {
            "species": name,
            "explorer_url": explorer_url("species", name),
            "extract_count": len(refs),
        }
        if zh := self.sp_zh.get(name):
            result["common_name_zh"] = zh
        if en := self.sp_en.get(name):
            result["common_name_en"] = en
        if (fm := first.get("fm")) is not None:
            result["family"] = self.families[fm]
        if k := first.get("k"):
            result["kingdom"] = k
        if o := first.get("ord"):
            result["order"] = o

        extracts = []
        for ref in refs:
            it = self.items[ref]
            e: dict = {"ref_no": ref, "inci_name": it["n"]}
            if pt := it.get("pt"):
                e["plant_parts"] = pt
            if pr := it.get("pr"):
                e["process"] = pr
            extracts.append(e)
        result["extracts"] = extracts

        cpd_count = 0
        for cpd in self.compounds.values():
            if cpd.get("top_sp"):
                for sp_entry in cpd["top_sp"]:
                    if sp_entry[0] == name:
                        cpd_count += 1
                        break
        result["compound_count"] = cpd_count
        return result

    def get_family_info(self, name: str) -> dict | None:
        fam_idx = None
        for i, f in enumerate(self.families):
            if f.lower() == name.lower():
                fam_idx = i
                name = f
                break
        if fam_idx is None:
            return None

        refs = self.by_family.get(fam_idx, [])
        result: dict = {
            "family": name,
            "explorer_url": explorer_url("family", name),
            "extract_count": len(refs),
        }
        if zh := self.fam_zh.get(name):
            result["common_name_zh"] = zh
        if en := self.fam_en.get(name):
            result["common_name_en"] = en

        species = set()
        fn_counter: dict[int, int] = {}
        restricted = 0
        for ref in refs:
            it = self.items[ref]
            if sp := it.get("sp"):
                species.add(sp)
            for fi in it.get("f", []):
                fn_counter[fi] = fn_counter.get(fi, 0) + 1
            if it.get("re"):
                restricted += 1

        result["species_count"] = len(species)
        result["species_list"] = sorted(species)

        top_fns = sorted(fn_counter.items(), key=lambda x: -x[1])[:10]
        result["top_functions"] = [
            {"function": self.functions[fi], "count": c} for fi, c in top_fns
        ]
        result["restriction_rate"] = round(restricted / len(refs), 3) if refs else 0
        return result

    def get_regulation(self, ref_no: str) -> dict | None:
        it = self.items.get(ref_no)
        if not it:
            return None
        result: dict = {
            "ref_no": ref_no,
            "inci_name": it["n"],
            "explorer_url": explorer_url("ingredient", ref_no),
        }
        re_text = it.get("re")
        if not re_text:
            result["restriction"] = None
            return result

        result["restriction_text"] = re_text
        parsed: dict = {}
        if "/" in re_text and len(re_text) < 20:
            parts = re_text.split("/")
            annex_map = {"II": "II (Prohibited)", "III": "III (Restricted)",
                         "IV": "IV (Colourants)", "V": "V (Preservatives)",
                         "VI": "VI (UV Filters)"}
            parsed["annex"] = annex_map.get(parts[0], parts[0])
            parsed["entry"] = parts[1] if len(parts) > 1 else None
        result["parsed"] = parsed
        return result

    def analyze_list(self, ingredients: list[str]) -> dict:
        matched = []
        unmatched = []
        fn_dist: dict[str, int] = {}
        fam_dist: dict[str, int] = {}
        bio_count = 0
        restricted_count = 0

        for raw in ingredients:
            name = raw.strip()
            if not name:
                continue
            upper = name.upper()
            ref = self.by_inci.get(upper)
            if not ref:
                normalized = "".join(upper.split())
                for inci, r in self.by_inci.items():
                    if "".join(inci.split()) == normalized:
                        ref = r
                        break
            if not ref:
                for inci, r in self.by_inci.items():
                    if upper in inci or inci in upper:
                        ref = r
                        break

            if ref:
                it = self.items[ref]
                fns = [self.functions[i] for i in it.get("f", [])]
                entry: dict = {
                    "input": name,
                    "ref_no": ref,
                    "inci_name": it["n"],
                    "functions": fns,
                }
                if (fm := it.get("fm")) is not None:
                    fam = self.families[fm]
                    entry["family"] = fam
                    fam_dist[fam] = fam_dist.get(fam, 0) + 1
                if re := it.get("re"):
                    entry["restriction"] = re
                    restricted_count += 1
                if it.get("sp"):
                    bio_count += 1
                for fn in fns:
                    fn_dist[fn] = fn_dist.get(fn, 0) + 1
                matched.append(entry)
            else:
                unmatched.append(name)

        total = len(matched) + len(unmatched)
        return {
            "matched": matched,
            "unmatched": unmatched,
            "summary": {
                "total": total,
                "matched_count": len(matched),
                "unmatched_count": len(unmatched),
                "bio_source_count": bio_count,
                "restricted_count": restricted_count,
                "function_distribution": dict(sorted(fn_dist.items(), key=lambda x: -x[1])),
                "family_distribution": dict(sorted(fam_dist.items(), key=lambda x: -x[1])),
            },
        }
