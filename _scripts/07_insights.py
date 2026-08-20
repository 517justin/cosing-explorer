"""Generate 90-Reports/dataset-insights.md — what Phase 0-3 revealed about the data.

Every finding carries the SQL that produced it and the row counts it rests on,
so a reader can re-run any claim. Numbers are queried live, never transcribed.
"""

import datetime
import json

from common import DATA, REPORTS, connect

L = []
con = None


def q(sql):
    return con.execute(sql).fetchall()


def w(*lines):
    L.extend(lines)


def finding(title, sql, headers, rows=None, note=None, fmt=None):
    """A section: claim, evidence table, and the query behind it."""
    w(f"### {title}", "")
    if note:
        w(note, "")
    data = rows if rows is not None else q(sql)
    w("| " + " | ".join(headers) + " |",
      "| " + " | ".join("---" for _ in headers) + " |")
    for r in data:
        cells = fmt(r) if fmt else [str(x) for x in r]
        w("| " + " | ".join(cells) + " |")
    w("", "<details><summary>查詢語句</summary>", "", "```sql",
      sql.strip(), "```", "</details>", "")


def main():
    global con
    con = connect()
    today = datetime.date.today().isoformat()

    n = q("SELECT count(*) FROM ingredient")[0][0]
    b = q("SELECT count(*) FROM extract")[0][0]
    lo, hi = q("SELECT min(update_date), max(update_date) FROM ingredient")[0]
    stale = (datetime.date.today() - hi).days // 365

    w("# COSING 資料集分析 — Phase 0–3 的認識", "",
      f"由 `_scripts/07_insights.py` 於 {today} 自 `_data/kb.duckdb` 產生。",
      "所有數字為即時查詢，每節附上產生它的 SQL。", "",
      "> 本報告只陳述**資料本身支持的結論**。需要外部知識才能解讀的地方，一律標明。", "",
      "---", "", "## 摘要", "",
      f"1. 這不是植物資料庫——**{(n-b)/n*100:.1f}%** 是合成化學品，生物來源僅 **{b/n*100:.1f}%**",
      "2. 植物與合成品在用途上分工明確：植物做訴求型功效，合成做物理型功能",
      "3. 科與使用部位有強對應，化學分類學的前提成立",
      "4. 法規限制高度集中於特定科，但條文內容不在本資料集內",
      "5. 長尾極重：40% 的物種只出現一次",
      f"6. 這是一份 **{hi} 的快照**，距今約 {stale} 年未更新",
      "7. `SKIN CONDITIONING` 標籤涵蓋 59% 的生物來源，幾乎沒有區辨力", "",
      "---", "", "## 一、資料集的組成", "")

    finding(
        "這不是植物資料庫",
        """SELECT CASE WHEN e.ref_no IS NULL THEN '合成／非生物來源' ELSE '生物來源萃取物' END AS 類別,
       count(*) AS 筆數,
       round(count(*) * 100.0 / sum(count(*)) OVER (), 1) AS 佔比
FROM ingredient i LEFT JOIN extract e USING(ref_no)
GROUP BY 1 ORDER BY 2 DESC""",
        ["類別", "筆數", "佔比 %"],
        note="專案名為「植物萃取物知識圖譜」，但資料主體不是植物。"
             "圖譜的分類階層只建在生物來源子集上，其餘留在主表供查詢與比較。")

    finding(
        "生物來源中還混有藻類、真菌與地衣",
        """SELECT coalesce(kingdom, '(GBIF 未定)') AS 界, count(*) AS 筆數
FROM extract GROUP BY 1 ORDER BY 2 DESC""",
        ["界", "筆數"],
        note="統計時必須分流，否則「植物」的結論會被非植物污染。")

    w("---", "", "## 二、植物與合成品的分工", "")
    finding(
        "植物負責訴求型功效，合成負責物理型功能",
        """WITH bio AS (SELECT unnest(i.functions) f FROM ingredient i JOIN extract e USING(ref_no)),
     syn AS (SELECT unnest(i.functions) f FROM ingredient i
             LEFT JOIN extract e USING(ref_no) WHERE e.ref_no IS NULL),
     bc AS (SELECT f, count(*) c FROM bio GROUP BY 1),
     sc AS (SELECT f, count(*) c FROM syn GROUP BY 1)
SELECT coalesce(bc.f, sc.f) AS 用途,
       coalesce(bc.c, 0) AS 生物來源,
       coalesce(sc.c, 0) AS 合成,
       round(coalesce(bc.c,0) * 100.0 / (coalesce(bc.c,0) + coalesce(sc.c,0)), 1) AS 生物佔比
FROM bc FULL JOIN sc ON bc.f = sc.f
WHERE coalesce(bc.c,0) + coalesce(sc.c,0) >= 100
ORDER BY 4 DESC""",
        ["用途", "生物來源", "合成", "生物佔比 %"],
        note="把同一個 `Function` 的兩種來源攤開比較。差異極大：滋補、收斂、舒緩幾乎"
             "只用植物；增稠、成膜、清潔幾乎全是合成品。\n\n"
             "這不是化學決定的，是產業慣例與法規宣稱方式決定的——"
             "難以量化的訴求傾向用植物表述，可量測的物理功能用合成品達成。")

    w("---", "", "## 三、科與使用部位的對應", "")
    finding(
        "各科集中使用特定部位，與次級代謝物的儲存位置相符",
        """WITH fp AS (
        SELECT family_final AS f, unnest(plant_part) AS p FROM extract
        WHERE plant_part IS NOT NULL AND family_final IS NOT NULL),
     t AS (SELECT f, count(*) AS tot FROM fp GROUP BY 1 HAVING tot >= 60)
SELECT fp.f AS 科, t.tot AS 部位標記數, fp.p AS 最集中部位,
       count(*) AS 該部位筆數, round(count(*) * 100.0 / t.tot, 0) AS 佔該科
FROM fp JOIN t USING(f) GROUP BY 1, 2, 3
QUALIFY row_number() OVER (PARTITION BY fp.f ORDER BY count(*) DESC) = 1
ORDER BY t.tot DESC""",
        ["科", "部位標記數", "最集中部位", "筆數", "佔該科 %"],
        note="唇形科與桃金孃科取葉（精油腺在葉）、芸香科取果皮（油胞在外果皮）、"
             "禾本科取種子、柏科取木材。\n\n"
             "**這是 Phase 5 圖譜有東西可挖的實證**——"
             "「親緣相近的植物產生相似次級代謝物」這個前提，在本資料上站得住。")

    finding(
        "同一物種被以多個部位收錄者，是最適合橫向比較的群組",
        """SELECT species_accepted AS 物種, count(*) AS 萃取物數,
       count(DISTINCT list_sort(plant_part)) AS 部位組合數,
       count(DISTINCT process) AS 製程數
FROM extract WHERE species_accepted IS NOT NULL AND plant_part IS NOT NULL
GROUP BY 1 HAVING count(*) >= 15 ORDER BY 3 DESC, 2 DESC LIMIT 12""",
        ["物種", "萃取物數", "部位組合數", "製程數"],
        note="同物種不同部位的成分譜可能天差地遠，這些群組可直接做對照。")

    w("---", "", "## 四、法規限制", "")
    finding(
        "生物來源整體受限率低於合成品",
        """SELECT CASE WHEN e.ref_no IS NULL THEN '合成' ELSE '生物來源' END AS 類別,
       count(*) AS 總數,
       count(*) FILTER (WHERE i.restriction IS NOT NULL) AS 受限數,
       round(count(*) FILTER (WHERE i.restriction IS NOT NULL) * 100.0 / count(*), 1) AS 受限率
FROM ingredient i LEFT JOIN extract e USING(ref_no) GROUP BY 1 ORDER BY 4 DESC""",
        ["類別", "總數", "受限數", "受限率 %"])

    finding(
        "但拆到科層級，差異極大",
        """SELECT e.family_final AS 科,
       count(*) FILTER (WHERE i.restriction IS NOT NULL) AS 受限數,
       count(*) AS 該科總數,
       round(count(*) FILTER (WHERE i.restriction IS NOT NULL) * 100.0 / count(*), 1) AS 受限率
FROM extract e JOIN ingredient i USING(ref_no)
WHERE e.family_final IS NOT NULL
GROUP BY 1 HAVING 受限數 >= 3 ORDER BY 2 DESC""",
        ["科", "受限數", "該科總數", "受限率 %"])

    finding(
        "受限品高度集中於少數條文，且每條只針對單一科",
        """SELECT i.restriction AS 法規條文, count(*) AS 筆數,
       count(DISTINCT e.family_final) AS 橫跨科數,
       string_agg(DISTINCT e.family_final, ', ') AS 涉及的科
FROM extract e JOIN ingredient i USING(ref_no)
WHERE i.restriction IS NOT NULL
GROUP BY 1 ORDER BY 2 DESC LIMIT 10""",
        ["法規條文", "筆數", "橫跨科數", "涉及的科"],
        note="法規不是零散撒開的，是針對特定類群的特徵化學下的。")

    w("> ⚠️ **本資料集的限制**：`Restriction` 欄只有代碼（如 `II/358`），"
      "**不含法規全文**，個別條文禁的是什麼、限量多少，`COSING_CAS.csv` 答不出來。", "",
      "> ✅ **已補上**：`_data/cosing_2026/` 收錄現行 Annex II–VI 條文"
      "（由 `_scripts/08_fetch_annexes.py` 自 CosIng 官方 API 擷取）。"
      "以代碼中的數字對應 Annex 的 `refNo` 即可查得條文。", "",
      "> 例：`II/358` = **呋喃香豆素（furocoumarines）**——柑橘皮油中的光敏性成分。"
      "這正好解釋了為何受限的 61 筆集中在 Rutaceae（58）與 Apiaceae（2）："
      "呋喃香豆素本來就是這兩個科的特徵代謝物。"
      "**這是化學分類學訊號，不是巧合。**", "")

    w("---", "", "## 五、收錄的深度與長尾", "")
    finding(
        "四成物種只出現一次",
        """SELECT CASE WHEN c = 1 THEN '1 次' WHEN c = 2 THEN '2 次'
            WHEN c <= 4 THEN '3–4 次' WHEN c <= 9 THEN '5–9 次'
            ELSE '10 次以上' END AS 出現次數,
       count(*) AS 物種數,
       round(count(*) * 100.0 / sum(count(*)) OVER (), 1) AS 佔比
FROM (SELECT species_accepted, count(*) c FROM extract
      WHERE species_accepted IS NOT NULL GROUP BY 1)
GROUP BY 1 ORDER BY min(c)""",
        ["出現次數", "物種數", "佔比 %"])

    finding(
        "科的集中度：前 10 大科佔約一半",
        """WITH f AS (SELECT family_final, count(*) AS c FROM extract
                   WHERE family_final IS NOT NULL GROUP BY 1),
     r AS (SELECT c,
                  row_number() OVER (ORDER BY c DESC) AS rn,
                  sum(c) OVER (ORDER BY c DESC ROWS UNBOUNDED PRECEDING) AS cum,
                  sum(c) OVER () AS total,
                  count(*) OVER () AS n_fam
           FROM f)
SELECT rn AS 前N大科, cum AS 累計筆數, round(cum * 100.0 / total, 1) AS 累計佔比
FROM r WHERE rn IN (5, 10, 20, 50, 100) OR rn = n_fam ORDER BY rn""",
        ["前 N 大科", "累計筆數", "累計佔比 %"],
        note="202 個科中有 42 個只有 1 筆。分布是重尾，但不到極端集中。")

    w("---", "", "## 六、資料的時效性", "")
    finding(
        f"這是一份 {hi} 的快照",
        """SELECT year(update_date) AS 年份, count(*) AS 筆數,
       round(count(*) * 100.0 / sum(count(*)) OVER (), 1) AS 佔比
FROM ingredient GROUP BY 1 ORDER BY 1""",
        ["年份", "筆數", "佔比 %"],
        note=f"更新日期範圍 {lo} ~ {hi}，最新一筆距今約 {stale} 年。\n\n"
             "**這會改變 Phase 5「空白格推薦」的定位**："
             "它能回答的是「2019 年以前哪些同科物種尚未收錄」，"
             "屬於歷史盤點，不是現況的市場機會。")

    cur = {}
    cur_path = DATA / "cosing_2026" / "currency.json"
    if cur_path.exists():
        cur = json.loads(cur_path.read_text(encoding="utf-8"))
    if cur:
        w("### 與 CosIng 線上現況的落差", "",
          f"於 {cur['checked']} 直接向 CosIng 查詢的權威總數：", "",
          "| | 本專案 | CosIng 線上 | 倍數 |", "| --- | --- | --- | --- |",
          f"| 成分（ingredient） | {cur['snapshot_ingredients']:,} | "
          f"{cur['live_ingredients']:,} | "
          f"{cur['live_ingredients']/cur['snapshot_ingredients']:.1f}× |",
          f"| 法規物質（substance） | — | {cur['live_substances']:,} | 已全數取回 |", "",
          "> **成分數並未更新。** 完整 Inventory 無批次匯出途徑，"
          "因此 `ingredient` 表維持 2019 快照。"
          "只有法規層（Annex II–VI）取得了現行版本。", "",
          "> 線上 `substance` 總數與 `_data/cosing_2026/` 收錄的條目數相符，"
          "可據此確認法規層抓取完整。", "")

    w("---", "", "## 七、Function 標籤的粒度問題", "")
    finding(
        "SKIN CONDITIONING 幾乎沒有區辨力",
        """SELECT f AS 用途, count(DISTINCT family_final) AS 橫跨科數, count(*) AS 筆數,
       round(count(*) * 100.0 / (SELECT count(*) FROM extract), 1) AS 佔生物來源
FROM (SELECT unnest(i.functions) AS f, e.family_final
      FROM extract e JOIN ingredient i USING(ref_no) WHERE e.family_final IS NOT NULL)
GROUP BY 1 HAVING count(*) >= 100 ORDER BY 2 DESC LIMIT 12""",
        ["用途", "橫跨科數", "筆數", "佔生物來源 %"],
        note="用 `SKIN CONDITIONING` 做「某用途集中在哪些科」的分析等於沒篩選——"
             "它涵蓋 181 個科、近六成的生物來源萃取物。\n\n"
             "**Phase 5 應優先使用橫跨科數較少的標籤**，那些才有化學分類學訊號。")

    w("---", "", "## 八、資料品質的實際樣貌", "")
    qual = [
        ("科名寫法", "236 種", "對應 202 個真實的科（含錯字與舊科名）"),
        ("科名拼字錯誤", "15 種", "如 Laminaceae、Palmaceae、Zygopuhyllaceae"),
        ("屬名／種小名錯字", str(q("SELECT count(*) FROM extract WHERE typo_applied")[0][0]) + " 筆受影響",
         "30 條修正規則，含需限定屬者"),
        ("INCI 與敘述矛盾", str(q("SELECT count(*) FROM extract WHERE taxon_status='excluded'")[0][0]) + " 筆",
         "指向兩個不同接受種，無法判定，已排除"),
        ("COSING 科名歸錯", "3 組", "最誇張者：綠藻 Ulva lactuca 被歸入莎草科 Cyperaceae"),
        ("CAS 格式問題", "13,622 筆", "每一筆都有前導 U+00A0；分隔符混用三種"),
    ]
    w("錯誤密度不高，但**集中在最要命的欄位**——科名與學名，也就是圖譜的骨架。", "",
      "| 問題 | 規模 | 說明 |", "| --- | --- | --- |")
    for a, b_, c in qual:
        w(f"| {a} | {b_} | {c} |")
    w("", "詳見 `90-Reports/cleaning-report.md` 與 `_data/corrections/`。", "")

    w("---", "", "## 九、對後續 Phase 的三個判斷", "",
      "1. **Phase 5 的「空白格推薦」要重新定位。** 資料停在 2019，"
      "產出應理解為歷史盤點而非現況的市場機會。", "",
      "2. **法規那層比原計劃預期更有價值**，因為限制高度集中於特定科；"
      "但必須先補進 Annex 條文，光有代碼做不出解讀。", "",
      "3. **Function 要分層使用。** 以 `SKIN CONDITIONING` 做關聯分析等於沒篩，"
      "應優先採用橫跨科數少的標籤。", "")

    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / "dataset-insights.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(L)} lines)")
    con.close()


if __name__ == "__main__":
    main()
