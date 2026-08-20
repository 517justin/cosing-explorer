"""Phase 4b - attach chemical structures by CAS number via PubChem.

The plan's second enrichment path, and the one that reaches the parts LOTUS
cannot. LOTUS covers species, so it serves the botanical rows; PubChem is keyed
on CAS, so it serves everything with a CAS -- including the synthetic majority
that has no biological source at all.

Rate limiting follows PubChem's stated policy: no more than 5 requests a second
and no more than 400 a minute. Three workers with a per-request delay lands
around 4/s, comfortably inside both. Responses are cached on disk, so a re-run
costs nothing and an interrupted run resumes where it stopped.

A CAS that PubChem cannot resolve is recorded as not-found rather than dropped:
the distinction between "no structure published" and "we did not ask" has to
survive, the same way it does for LOTUS coverage.
"""

import json
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from common import DATA, REPORTS, SUFFIX, T, connect

CACHE = DATA / "pubchem_cache.json"
API = ("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}"
       "/property/MolecularFormula,InChIKey,ConnectivitySMILES,MolecularWeight/JSON")
WORKERS = 3
DELAY = 0.75            # per worker -> ~4 requests/second overall

_lock = threading.Lock()


def load_cache():
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def fetch(cas):
    url = API.format(urllib.parse.quote(cas))
    req = urllib.request.Request(url, headers={"User-Agent": "cosing-kg/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=60) as fh:
            d = json.load(fh)
        p = d.get("PropertyTable", {}).get("Properties", [{}])[0]
        out = {"cid": p.get("CID"), "formula": p.get("MolecularFormula"),
               "inchikey": p.get("InChIKey"), "smiles": p.get("ConnectivitySMILES"),
               "mw": p.get("MolecularWeight"), "found": bool(p.get("CID"))}
    except urllib.error.HTTPError as e:
        # 404 is a real answer: PubChem has no compound under that CAS.
        out = {"found": False, "error": None if e.code == 404 else f"HTTP {e.code}"}
    except Exception as e:                       # network hiccup, keep going
        out = {"found": False, "error": str(e)[:80]}
    time.sleep(DELAY)
    return out


def main():
    # DuckDB allows a single writer, so the connection is opened to read the CAS
    # list, closed for the long fetch, and reopened to write. Holding it across
    # a 40-minute download locks every other script out of the database.
    ing = T("ingredient")
    con = connect()
    cas_list = [r[0] for r in con.execute(
        f"SELECT DISTINCT cas_primary FROM {ing} "
        f"WHERE cas_primary IS NOT NULL ORDER BY 1").fetchall()]
    con.close()

    cache = load_cache()
    todo = [c for c in cas_list if c not in cache]
    print(f"unique CAS: {len(cas_list):,}   cached: {len(cas_list) - len(todo):,}   "
          f"to fetch: {len(todo):,}", flush=True)
    if todo:
        eta = len(todo) * DELAY / WORKERS / 60
        print(f"  pacing ~{WORKERS/DELAY:.1f} req/s (PubChem allows 5), "
              f"ETA ~{eta:.0f} min", flush=True)

    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for cas, res in zip(todo, pool.map(fetch, todo)):
            with _lock:
                cache[cas] = res
            done += 1
            if done % 500 == 0:
                CACHE.write_text(json.dumps(cache, ensure_ascii=False),
                                 encoding="utf-8")
                print(f"    {done:,}/{len(todo):,}", flush=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    con = connect()                              # reopen only to write
    tbl = f"cas_structure{SUFFIX}"
    con.execute(f"DROP TABLE IF EXISTS {tbl}")
    con.execute(f"""CREATE TABLE {tbl} (
        cas VARCHAR PRIMARY KEY, cid BIGINT, formula VARCHAR, inchikey VARCHAR,
        smiles VARCHAR, mw VARCHAR, found BOOLEAN, error VARCHAR)""")
    con.executemany(
        f"INSERT INTO {tbl} VALUES (?,?,?,?,?,?,?,?)",
        [[c, cache[c].get("cid"), cache[c].get("formula"), cache[c].get("inchikey"),
          cache[c].get("smiles"), str(cache[c].get("mw") or "") or None,
          bool(cache[c].get("found")), cache[c].get("error")]
         for c in cas_list if c in cache])

    _report(con, ing, tbl, len(cas_list))
    con.close()


def _report(con, ing, tbl, n_cas):
    q = lambda s: con.execute(s).fetchall()
    found = q(f"SELECT count(*) FROM {tbl} WHERE found")[0][0]
    err = q(f"SELECT count(*) FROM {tbl} WHERE error IS NOT NULL")[0][0]
    ex = T("extract")
    rows_tot = q(f"SELECT count(*) FROM {ing}")[0][0]
    rows_hit = q(f"""SELECT count(*) FROM {ing} i JOIN {tbl} t
                     ON t.cas = i.cas_primary WHERE t.found""")[0][0]
    bio_tot = q(f"SELECT count(*) FROM {ex}")[0][0]
    bio_hit = q(f"""SELECT count(*) FROM {ex} e JOIN {ing} i USING(ref_no)
                    JOIN {tbl} t ON t.cas = i.cas_primary WHERE t.found""")[0][0]
    syn_tot = rows_tot - bio_tot
    syn_hit = rows_hit - bio_hit

    print(f"\nCAS resolved          : {found:,}/{n_cas:,} ({found/n_cas*100:.1f}%)")
    print(f"  network errors      : {err}")
    print(f"  成分有結構          : {rows_hit:,}/{rows_tot:,} ({rows_hit/rows_tot*100:.1f}%)")
    print(f"    生物來源          : {bio_hit:,}/{bio_tot:,} ({bio_hit/bio_tot*100:.1f}%)")
    print(f"    合成              : {syn_hit:,}/{syn_tot:,} ({syn_hit/syn_tot*100:.1f}%)")

    L = [f"# Phase 4b — PubChem 結構富集{' (2026)' if SUFFIX else ''}", "",
         "以 CAS 號向 PubChem 取得分子式、InChIKey、SMILES 與分子量。"
         "這條路徑補的是 LOTUS 到不了的地方——LOTUS 以物種為鍵，"
         "PubChem 以 CAS 為鍵，因此能涵蓋沒有生物來源的合成成分。", "",
         "## 一、覆蓋率", "",
         "| 項目 | 值 |", "| --- | --- |",
         f"| 不重複 CAS | {n_cas:,} |",
         f"| PubChem 查得到 | **{found:,}**（{found/n_cas*100:.1f}%）|",
         f"| 網路錯誤（非查無） | {err} |", "",
         "| 成分類別 | 有結構 | 總數 | 比例 |", "| --- | --- | --- | --- |",
         f"| 生物來源萃取物 | {bio_hit:,} | {bio_tot:,} | {bio_hit/bio_tot*100:.1f}% |",
         f"| 合成／其他 | {syn_hit:,} | {syn_tot:,} | {syn_hit/syn_tot*100:.1f}% |",
         f"| **合計** | **{rows_hit:,}** | **{rows_tot:,}** | **{rows_hit/rows_tot*100:.1f}%** |", "",
         "> 生物來源的覆蓋率必然偏低：萃取物是**混合物**，"
         "一個 CAS 對應的是「某某植物萃取物」這個材料，而非單一分子。"
         "萃取物的化學層應以 LOTUS（物種→成分）為主，本表為輔。", "",
         "## 二、查無結構者", "",
         f"**{n_cas - found:,}** 個 CAS 在 PubChem 中查無對應化合物。"
         "多為萃取物或聚合物的集合性 CAS，本來就沒有單一結構。"
         "這些以 `found = false` 記錄，**未被丟棄**，"
         "以免「查無」與「未查」混為一談。", ""]

    checks = [
        (f"{tbl} 已建立", q(f"SELECT count(*) FROM {tbl}")[0][0] > 0),
        ("CAS 解析率 > 40%", found / n_cas > 0.40),
        ("查無者以 found=false 保留，未丟棄",
         q(f"SELECT count(*) FROM {tbl} WHERE NOT found")[0][0] == n_cas - found),
        ("網路錯誤數為 0", err == 0),
    ]
    L += ["## 三、驗收檢查", "", "| 檢查項 | 結果 |", "| --- | --- |"]
    L += [f"| {lab} | {'✅ 通過' if ok else '❌ 失敗'} |" for lab, ok in checks]
    print("\n驗收：")
    for lab, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {lab}")

    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / f"pubchem-report{SUFFIX}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
