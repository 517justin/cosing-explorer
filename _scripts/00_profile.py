"""Phase 0 - regenerate 90-Reports/data-profile.md from the loaded database.

Kept as a script rather than a one-off analysis so the profile can be re-run
against a newer COSING export and diffed.
"""

import re
from collections import Counter

from common import FAMILY_RE, REPORTS, connect

PART_WORDS = re.compile(
    r"\b(leaf|leaves|root|roots|seed|seeds|flower|flowers|fruit|bark|stem|wood"
    r"|herb|bulb|rhizome|peel|kernel|shoot|sprout|twig|bud)\b",
    re.I,
)
NON_PLANT = {
    "algae": ["Bangiaceae", "Gelidiaceae", "Fucaceae", "Furaceae", "Laminariaceae",
              "Corallinaceae", "Sargassaceae", "Gigartinaceae", "Codiaceae",
              "Caulerpaceae", "Chlorellaceae", "Oocystaceae", "Hypneaceae",
              "Rhodomelaceae", "Rhodymeniaceae", "Solieriaceae", "Porphyridaceae",
              "Himanthaliaceae", "Bonnemaisoniaceae"],
    "fungi": ["Agaricaceae", "Boletaceae", "Polyporaceae", "Tuberaceae"],
    "lichen": ["Parmeliaceae", "Usneaceae", "Cladoniaceae"],
    "yeast": ["Saccharomycetaceae"],
    "moss": ["Sphagnaceae"],
}


def main():
    con = connect()
    q = lambda s, *a: con.execute(s, list(a)).fetchall()
    n = q("SELECT count(*) FROM ingredient")[0][0]
    bio = q("SELECT count(*) FROM extract")[0][0]

    L = ["# COSING 資料剖析報告", "",
         f"由 `_scripts/00_profile.py` 自 `_data/kb.duckdb` 產生。原始檔 "
         f"`_data/COSING_CAS.csv`（唯讀）。", "",
         "## 一、規模", "",
         "| 項目 | 值 |", "| --- | --- |",
         f"| 成分總列數 | {n:,} |",
         f"| 生物來源萃取物 | {bio:,}（{bio/n*100:.1f}%）|",
         f"| 純化學品 | {n-bio:,}（{(n-bio)/n*100:.1f}%）|", ""]

    L += ["## 二、欄位剖析", "",
          "| 欄位 | 空值率 | 唯一值 | 最大長度 |", "| --- | --- | --- | --- |"]
    for col in ["ref_no", "inci_name", "inn_name", "ph_eur_name", "cas_raw",
                "description", "restriction", "function_raw", "update_date"]:
        e, u, m = q(
            f"SELECT count(*) FILTER (WHERE {col} IS NULL OR CAST({col} AS VARCHAR)=''),"
            f" count(DISTINCT {col}), max(length(CAST({col} AS VARCHAR))) FROM ingredient"
        )[0]
        L += [f"| `{col}` | {e/n*100:.1f}% | {u:,} | {m} |"]

    d0, d1 = q("SELECT min(update_date), max(update_date) FROM ingredient")[0]
    L += ["", f"`update_date` 範圍：{d0} ~ {d1}", ""]

    L += ["## 三、CAS 欄位品質", "", "| 項目 | 列數 |", "| --- | --- |"]
    for label, sql in [
        ("多值 CAS（>1 個編號）", "SELECT count(*) FROM ingredient WHERE len(cas_numbers)>1"),
        ("標記 (generic)", "SELECT count(*) FROM ingredient WHERE cas_is_generic"),
        ("無可解析 CAS", "SELECT count(*) FROM ingredient WHERE cas_primary IS NULL"),
        ("含無法解析的殘留文字", "SELECT count(*) FROM ingredient WHERE cas_unparsed IS NOT NULL"),
    ]:
        L += [f"| {label} | {q(sql)[0][0]} |"]
    L += ["", "> 原始檔中**每一列**的 CAS 欄都帶前導 U+00A0（不斷行空白），"
          "且分隔符混用 `;`、` / `、`,`。載入時一律正規化。", ""]

    L += ["## 四、生物來源列的解析狀態", "",
          "| taxon_status | 列數 | 說明 |", "| --- | --- | --- |"]
    notes = {
        "agree": "INCI 與敘述兩路徑一致，自動採用",
        "inci_not_binomial": "INCI 為俗名/商品名，學名取自敘述",
        "species_mismatch": "兩路徑物種不同，待人工裁決",
        "genus_level_entry": "INCI 只到屬層級（如 CITRUS SPECIES）",
        "inci_truncated": "INCI 截斷了種下名，敘述較完整",
        "hyphen_split": "INCI 把連字號學名拆成兩個詞",
        "spelling_variant": "編輯距離 1 的拼字差異，採用 INCI 寫法",
        "genus_mismatch": "兩路徑屬不同，待人工裁決",
        "desc_unparsed": "敘述無可解析學名",
    }
    for status, c in q("SELECT taxon_status,count(*) FROM extract GROUP BY 1 ORDER BY 2 DESC"):
        L += [f"| `{status}` | {c} | {notes.get(status,'')} |"]

    L += ["", "## 五、科名分布（正規化後）", "",
          "| 科 | 萃取物數 | 原始寫法數 |", "| --- | --- | --- |"]
    for f, c, v in q(
        "SELECT family_accepted, count(*) c, count(DISTINCT family_raw) v FROM extract "
        "WHERE family_accepted IS NOT NULL GROUP BY 1 ORDER BY c DESC LIMIT 20"
    ):
        L += [f"| {f} | {c} | {v} |"]

    L += ["", "## 六、非植物生物來源", "",
          "資料集名為「植物萃取物」，但實際含藻類、真菌、地衣、酵母與苔蘚。"
          "統計時必須分流，否則「植物」結論會被污染。", "",
          "| 類群 | 列數 |", "| --- | --- |"]
    for kind, fams in NON_PLANT.items():
        c = q("SELECT count(*) FROM extract WHERE family_raw IN "
              f"({','.join(['?']*len(fams))})", *fams)[0][0]
        if c:
            L += [f"| {kind} | {c} |"]

    L += ["", "## 七、用途（Function）受控詞彙", ""]
    fc = Counter()
    for (fl,) in q("SELECT functions FROM ingredient"):
        for f in fl or []:
            fc[f] += 1
    L += [f"共 **{len(fc)}** 個詞彙。前 20 名：", "",
          "| 用途 | 全庫 | 生物來源 |", "| --- | --- | --- |"]
    bfc = Counter()
    for (fl,) in q("SELECT i.functions FROM ingredient i JOIN extract e USING(ref_no)"):
        for f in fl or []:
            bfc[f] += 1
    for f, c in fc.most_common(20):
        L += [f"| {f} | {c} | {bfc.get(f,0)} |"]

    L += ["", "## 八、法規限制（Restriction）", ""]
    r = q("SELECT count(*) FROM ingredient WHERE restriction IS NOT NULL")[0][0]
    rb = q("SELECT count(*) FROM ingredient i JOIN extract e USING(ref_no) "
           "WHERE i.restriction IS NOT NULL")[0][0]
    L += [f"- 帶限制的成分：**{r:,}**（其中生物來源 **{rb}**）", "",
          "| Annex | 列數 |", "| --- | --- |"]
    ann = Counter()
    for (v,) in q("SELECT restriction FROM ingredient WHERE restriction IS NOT NULL"):
        m = re.match(r"^([IVX]+)/", v.strip())
        ann[m.group(1) if m else "其他"] += 1
    for k, c in ann.most_common():
        L += [f"| {k} | {c} |"]

    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "data-profile.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {REPORTS / 'data-profile.md'}  ({n:,} ingredients, {bio:,} extracts)")
    con.close()


if __name__ == "__main__":
    main()
