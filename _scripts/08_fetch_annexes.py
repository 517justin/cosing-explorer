"""Fetch the CosIng Annex II-VI substance lists (the current, live regulation).

Why this exists: `_data/COSING_CAS.csv` is a 2019 snapshot whose `Restriction`
column holds only citation codes such as 'II/358' -- no text. It cannot say what
is restricted or under what conditions. The Annex lists carry exactly that.

How it fetches: the CosIng site is an Angular app whose Annex pages offer
PDF/XLS/CSV export, built client-side from one call per annex to the
Commission's public search API. This script issues that same call -- six
requests in total, the same the export buttons make -- and writes the result
straight to disk. The apiKey is the one published in the site's own JavaScript.

Re-run to refresh. Each file records its fetch date; the payload also carries
CosIng's own `publicationDate` per substance.
"""

import csv
import json
import time
import urllib.request
import uuid
from datetime import date

from common import DATA

OUT = DATA / "cosing_2026"
# The API caps a page at 200 regardless of the pageSize asked for, so results
# are paged through explicitly rather than trusted to arrive in one response.
API = ("https://webgate.ec.europa.eu/es/search-api/rest/search"
       "?apiKey=285a77fd-1257-4271-8507-f0c6b2961203&text=*"
       "&pageSize={size}&pageNumber={page}")
PAGE_SIZE = 200
ANNEXES = ["II", "III", "IV", "V", "VI"]

# Metadata fields worth keeping, in report order. The API returns every value
# as a list, so they are flattened on the way out.
FIELDS = ["refNo", "annexNo", "inciName", "chemicalName", "innName", "phEurName",
          "casNo", "ecNo", "chemicalDescription", "identifiedIngredient",
          "functionName", "cosmeticRestriction", "maximumConcentration",
          "productTypeBodyParts", "otherRestrictions", "otherRegulations",
          "classificationInformation", "note", "colour", "perfuming",
          "publicationDate", "currentVersion"]


def post(query, sort, page=1):
    boundary = "----cosing" + uuid.uuid4().hex
    parts = []
    for name, value in (("query", query), ("sort", sort)):
        parts += [f"--{boundary}",
                  f'Content-Disposition: form-data; name="{name}"; filename="{name}"',
                  "Content-Type: application/json", "", value]
    parts += [f"--{boundary}--", ""]
    body = "\r\n".join(parts).encode("utf-8")
    req = urllib.request.Request(
        API.format(size=PAGE_SIZE, page=page), data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                 "User-Agent": "cosing-kg/0.1"})
    with urllib.request.urlopen(req, timeout=90) as fh:
        return json.load(fh)


def flatten(v):
    if isinstance(v, list):
        return " | ".join(str(x) for x in v if x not in (None, ""))
    return "" if v is None else str(v)


def count(item_type):
    """One cheap request for a totalResults, no payload wanted."""
    query = json.dumps({"bool": {"must": [{"term": {"itemType": item_type}}]}})
    sort = json.dumps([{"field": "refNo_digit", "order": "ASC"}])
    return post(query, sort, page=1).get("totalResults", 0)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fetched = date.today().isoformat()
    summary = []

    # Currency check: how far has the live inventory moved past our snapshot?
    live_ingredients = count("ingredient")
    live_substances = count("substance")
    print(f"live CosIng: {live_ingredients} ingredients, {live_substances} substances")
    (OUT / "currency.json").write_text(json.dumps({
        "checked": fetched,
        "live_ingredients": live_ingredients,
        "live_substances": live_substances,
        "snapshot_ingredients": 13622,
        "snapshot_date": "2019-11-21",
        "note": ("Only the annex (substance) layer is downloadable in bulk. "
                 "The ingredient inventory has no export, so ingredient counts "
                 "in this project remain the 2019 snapshot."),
    }, indent=1), encoding="utf-8")
    time.sleep(1.0)

    for annex in ANNEXES:
        query = json.dumps({"bool": {"must": [
            {"term": {"itemType": "substance"}},
            {"term": {"annexNo": annex}},
            {"term": {"officialJournalPublication": "Y"}}]}})
        sort = json.dumps([{"field": "refNo_digit", "order": "ASC"},
                           {"field": "refNo_letter", "order": "ASC"}])
        results, page, total = [], 1, None
        while True:
            data = post(query, sort, page)
            total = data.get("totalResults", 0)
            batch = data.get("results", [])
            results.extend(batch)
            if not batch or len(results) >= total:
                break
            page += 1
            time.sleep(0.5)
        if len(results) != total:
            raise SystemExit(
                f"annex {annex}: collected {len(results)} but API reports {total}")

        (OUT / f"annex_{annex}.json").write_text(
            json.dumps({"_fetched": fetched, "_annex": annex,
                        "_totalResults": total, "results": results},
                       ensure_ascii=False, indent=1), encoding="utf-8")

        rows = []
        for r in results:
            md = r.get("metadata", {})
            rows.append({f: flatten(md.get(f)) for f in FIELDS})
        with open(OUT / f"annex_{annex}.csv", "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)

        with_limit = sum(1 for r in rows if r["maximumConcentration"])
        summary.append((annex, total, len(rows), with_limit))
        print(f"  Annex {annex:<4} {total:>5} substances  "
              f"({with_limit} 有濃度上限)  -> annex_{annex}.csv")
        time.sleep(1.0)                       # one request per second, be polite

    ratio = live_ingredients / 13622
    (OUT / "README.md").write_text("\n".join([
        "# CosIng Annex II–VI（現行法規）", "",
        f"擷取日期：**{fetched}**　由 `_scripts/08_fetch_annexes.py` 產生，重跑即更新。", "",
        "## ⚠️ 只有法規層是新的", "",
        "| | 本專案 | CosIng 線上現況 |",
        "| --- | --- | --- |",
        f"| 成分（ingredient） | **13,622**（2019-11-21 快照） | "
        f"**{live_ingredients:,}** |",
        f"| 法規物質（substance） | — | **{live_substances:,}**（已全數取回）|",
        "",
        f"線上成分數是我們的 **{ratio:.1f} 倍**。完整 Inventory **無批次匯出**"
        "（搜尋強制關鍵字、結果頁無匯出鈕、data.europa.eu 舊資料集已失效），"
        "因此本專案的 `ingredient` 表**維持 2019 快照未更新**。", "",
        "## 為什麼需要這份資料", "",
        "`_data/COSING_CAS.csv` 是 2019 快照，`Restriction` 欄只有引用代碼"
        "（如 `II/358`），**沒有條文**，無法回答「限制的是什麼、限量多少」。"
        "本目錄補上那一層。", "",
        "## 內容", "",
        "| Annex | 名稱 | 物質數 | 有濃度上限 |",
        "| --- | --- | --- | --- |",
        "| II | 禁用物質 | %d | %d |" % (summary[0][1], summary[0][3]),
        "| III | 限用物質 | %d | %d |" % (summary[1][1], summary[1][3]),
        "| IV | 准用著色劑 | %d | %d |" % (summary[2][1], summary[2][3]),
        "| V | 准用防腐劑 | %d | %d |" % (summary[3][1], summary[3][3]),
        "| VI | 准用紫外線濾劑 | %d | %d |" % (summary[4][1], summary[4][3]),
        "", "## 來源", "",
        "歐盟執委會 CosIng 資料庫的公開搜尋 API，"
        "即該站 Annex 頁面 PDF/XLS/CSV 匯出鈕所呼叫的同一個端點。"
        "每個 Annex 一次請求，共 5 次。", "",
        "## 與 2019 快照的關係", "",
        "兩者**不要混用**。`COSING_CAS.csv` 保持唯讀且不變動；"
        "本目錄是獨立的現行法規層，以 `refNo` 對應舊資料 `restriction` 欄的代碼"
        "（`II/358` 的 `358` 即 Annex II 的 `refNo`）。", "",
    ]) + "\n", encoding="utf-8")
    print(f"\nwrote {OUT}/ ({len(ANNEXES)} annexes, fetched {fetched})")


if __name__ == "__main__":
    main()
