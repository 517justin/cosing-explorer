"""Join the current Annex II-VI regulation into the database.

Builds three things:

  regulation            one row per Annex substance entry (the legal text)
  ingredient_citation   ingredient -> annex entry, from two independent sources
  ingredient_cmr        CMR classifications mentioned in the 2019 restriction text

Two link paths, deliberately kept apart:

  snapshot_2019  parsed out of `ingredient.restriction`, which is how COSING
                 cited the annexes at the time our CSV was taken
  annex_2026     the current annex's own `identifiedIngredient` field, which
                 lists the COSING Ref Nos each entry applies to today

Comparing them shows what the regulation did since 2019 rather than assuming
the snapshot is still true.

The 2019 restriction column is free text, not a code. It carries 'Annex III/264'
and 'annex III/259' and bare 'III/110', multiple citations in one cell
('V/54 III/65'), CMR classifications mixed in with citations ('CMR1B II/656'),
inline legal notes after a dash, and entries that cite nothing at all
('Suspected carcinogen based on ECHA'). Every citation is extracted; whatever
does not parse is kept in `unparsed` rather than dropped.
"""

import csv
import re

from common import DATA, REPORTS, connect

ANNEX_DIR = DATA / "cosing_2026"
# Roman numeral alternation is ordered longest-first so VI is not read as V.
CITATION = re.compile(r"\b(?:annex\s+)?(VI|IV|V|III|II|I)\s*/\s*(\d+[a-z]?)\b", re.I)
CMR = re.compile(r"\bCMR\s*\.?\s*(1A|1B|2)\b|\bCarc\.?\s*(1A|1B|2)\b", re.I)

FIELDS = ["refNo", "annexNo", "inciName", "chemicalName", "innName", "phEurName",
          "casNo", "ecNo", "chemicalDescription", "identifiedIngredient",
          "functionName", "cosmeticRestriction", "maximumConcentration",
          "productTypeBodyParts", "otherRestrictions", "otherRegulations",
          "classificationInformation", "note", "colour", "perfuming",
          "publicationDate", "currentVersion"]


def load_regulation(con):
    rows = []
    for path in sorted(ANNEX_DIR.glob("annex_*.csv")):
        with open(path, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                rows.append({f: (r.get(f) or None) for f in FIELDS})
    if not rows:
        raise SystemExit(f"no annex CSVs in {ANNEX_DIR}; run 08_fetch_annexes.py")

    con.execute("DROP TABLE IF EXISTS regulation")
    con.execute("""
        CREATE TABLE regulation (
            annex_no VARCHAR, ref_no VARCHAR, substance VARCHAR,
            chemical_name VARCHAR, inn_name VARCHAR, ph_eur_name VARCHAR,
            cas_no VARCHAR, ec_no VARCHAR, description VARCHAR,
            identified_ingredients VARCHAR, function_name VARCHAR,
            cosmetic_restriction VARCHAR, max_concentration VARCHAR,
            product_type VARCHAR, other_restrictions VARCHAR,
            other_regulations VARCHAR, classification VARCHAR, note VARCHAR,
            colour VARCHAR, perfuming VARCHAR, publication_date VARCHAR,
            version VARCHAR,
            entry_seq INTEGER)""")
    order = ["annexNo", "refNo", "inciName", "chemicalName", "innName",
             "phEurName", "casNo", "ecNo", "chemicalDescription",
             "identifiedIngredient", "functionName", "cosmeticRestriction",
             "maximumConcentration", "productTypeBodyParts", "otherRestrictions",
             "otherRegulations", "classificationInformation", "note", "colour",
             "perfuming", "publicationDate", "currentVersion"]
    # One refNo can cover several distinct substances -- Annex II/38 lists three
    # different coal tar distillates -- so refNo is NOT a key. Every row is kept
    # and numbered within its (annex, refNo); the citation join is 1:many.
    from collections import Counter
    seq = Counter()
    payload = []
    for r in rows:
        key = (r["annexNo"], r["refNo"])
        seq[key] += 1
        payload.append([r[f] for f in order] + [seq[key]])
    con.executemany(
        f"INSERT INTO regulation VALUES ({','.join(['?'] * (len(order) + 1))})",
        payload)
    multi = sum(1 for v in seq.values() if v > 1)
    return len(rows), multi


def citations_2019(con):
    """Parse every annex citation out of the free-text restriction column."""
    out, cmr_rows, unparsed = [], [], []
    for ref_no, raw in con.execute(
            "SELECT ref_no, restriction FROM ingredient "
            "WHERE restriction IS NOT NULL").fetchall():
        found = CITATION.findall(raw)
        for annex, num in found:
            out.append((ref_no, annex.upper(), num.lower(), raw))
        for m in CMR.finditer(raw):
            cmr_rows.append((ref_no, (m.group(1) or m.group(2)).upper(), raw))
        if not found:
            unparsed.append((ref_no, raw))
    return out, cmr_rows, unparsed


def citations_2026(con):
    """The current annexes name the ingredients they apply to."""
    out = []
    for annex, ref, ids in con.execute(
            "SELECT annex_no, ref_no, identified_ingredients FROM regulation "
            "WHERE identified_ingredients IS NOT NULL").fetchall():
        for tok in ids.split("|"):
            tok = tok.strip()
            if tok.isdigit():
                out.append((int(tok), annex, ref))
    return out


def main():
    con = connect()
    total, multi = load_regulation(con)
    print(f"regulation table        : {total} entries "
          f"({multi} refNo 底下有多個物質，全數保留)")

    n_reg = total
    cit19, cmr, unparsed = citations_2019(con)
    cit26 = citations_2026(con)

    con.execute("DROP TABLE IF EXISTS ingredient_citation")
    con.execute("""
        CREATE TABLE ingredient_citation (
            ref_no INTEGER, annex_no VARCHAR, annex_ref VARCHAR,
            source VARCHAR, raw VARCHAR)""")
    con.executemany("INSERT INTO ingredient_citation VALUES (?,?,?,'snapshot_2019',?)",
                    cit19)
    con.executemany("INSERT INTO ingredient_citation VALUES (?,?,?,'annex_2026',NULL)",
                    [(r, a, n) for r, a, n in cit26])

    con.execute("DROP TABLE IF EXISTS ingredient_cmr")
    con.execute("CREATE TABLE ingredient_cmr (ref_no INTEGER, cmr_class VARCHAR, raw VARCHAR)")
    con.executemany("INSERT INTO ingredient_cmr VALUES (?,?,?)", cmr)

    con.execute("DROP TABLE IF EXISTS restriction_unparsed")
    con.execute("CREATE TABLE restriction_unparsed (ref_no INTEGER, raw VARCHAR)")
    con.executemany("INSERT INTO restriction_unparsed VALUES (?,?)", unparsed)

    _view(con)
    _report(con, n_reg, len(cit19), len(cit26), len(cmr), len(unparsed))
    con.close()


def _view(con):
    """One convenient join: extract row -> the legal text that applies to it."""
    con.execute("DROP VIEW IF EXISTS extract_regulation")
    con.execute("""
        CREATE VIEW extract_regulation AS
        SELECT e.ref_no, i.inci_name, e.family_final, e.species_accepted,
               e.plant_part, e.process,
               c.source, c.annex_no, c.annex_ref,
               r.substance          AS regulated_substance,
               r.max_concentration, r.product_type, r.other_restrictions,
               r.cosmetic_restriction, r.note
        FROM extract e
        JOIN ingredient i USING(ref_no)
        JOIN ingredient_citation c USING(ref_no)
        LEFT JOIN regulation r
               ON r.annex_no = c.annex_no AND r.ref_no = c.annex_ref""")
    # NOTE: a citation can match several regulation rows (one refNo, several
    # substances), so this view can return more rows than there are citations.


def _report(con, n_reg, n19, n26, n_cmr, n_unparsed):
    q = lambda s: con.execute(s).fetchall()

    resolved = q("""SELECT count(*) FROM (
                        SELECT DISTINCT c.ref_no, c.annex_no, c.annex_ref
                        FROM ingredient_citation c JOIN regulation r
                          ON r.annex_no=c.annex_no AND r.ref_no=c.annex_ref
                        WHERE c.source='snapshot_2019')""")[0][0]
    print(f"2019 citations parsed   : {n19}  (解析到現行條文 {resolved}, "
          f"{resolved/n19*100:.1f}%)")
    print(f"2026 annex -> ingredient: {n26}")
    print(f"CMR classifications     : {n_cmr}")
    print(f"restriction 無引用者     : {n_unparsed}")

    bio_now = q("""SELECT count(DISTINCT c.ref_no) FROM ingredient_citation c
                   JOIN extract e USING(ref_no) WHERE c.source='annex_2026'""")[0][0]
    bio_then = q("""SELECT count(DISTINCT c.ref_no) FROM ingredient_citation c
                    JOIN extract e USING(ref_no) WHERE c.source='snapshot_2019'""")[0][0]

    newly = q("""SELECT e.family_final, count(DISTINCT c.ref_no) n
                 FROM ingredient_citation c JOIN extract e USING(ref_no)
                 WHERE c.source='annex_2026' AND c.ref_no NOT IN (
                     SELECT ref_no FROM ingredient_citation WHERE source='snapshot_2019')
                 GROUP BY 1 ORDER BY n DESC LIMIT 12""")
    gone = q("""SELECT count(DISTINCT ref_no) FROM ingredient_citation
                WHERE source='snapshot_2019' AND ref_no NOT IN (
                    SELECT ref_no FROM ingredient_citation WHERE source='annex_2026')
                  AND ref_no IN (SELECT ref_no FROM extract)""")[0][0]

    top = q("""SELECT c.annex_no || '/' || c.annex_ref AS 條文,
                      substr(coalesce(r.substance, '(現行條文中查無)'), 1, 90) AS 內容,
                      count(DISTINCT c.ref_no) AS 萃取物數,
                      count(DISTINCT e.family_final) AS 科數
               FROM ingredient_citation c JOIN extract e USING(ref_no)
               LEFT JOIN regulation r ON r.annex_no=c.annex_no
                                     AND r.ref_no=c.annex_ref AND r.entry_seq=1
               WHERE c.source='annex_2026'
               GROUP BY 1,2 ORDER BY 3 DESC LIMIT 12""")
    fam = q("""SELECT e.family_final AS 科,
                      count(DISTINCT c.ref_no) AS 受限數,
                      count(DISTINCT e.ref_no) FILTER (WHERE TRUE) AS x
               FROM extract e LEFT JOIN ingredient_citation c
                 ON c.ref_no=e.ref_no AND c.source='annex_2026'
               WHERE e.family_final IS NOT NULL
               GROUP BY 1 HAVING 受限數 >= 3 ORDER BY 2 DESC LIMIT 12""")

    L = ["# 法規層 — 現行 Annex 與 2019 快照的對照", "",
         f"由 `_scripts/09_link_regulation.py` 產生。法規資料為 `_data/cosing_2026/`"
         f"（{n_reg} 條 Annex 條文），與唯讀的 2019 快照分開存放。", "",
         "## 一、兩條連結路徑", "",
         "| 來源 | 連結數 | 說明 |", "| --- | --- | --- |",
         f"| `snapshot_2019` | {n19} | 從 2019 `restriction` 欄解析出的引用，"
         f"其中 {resolved}（{resolved/n19*100:.1f}%）在現行條文中仍找得到 |",
         f"| `annex_2026` | {n26} | 現行 Annex 條文自己列出的適用成分編號 |", "",
         f"生物來源萃取物受限數：2019 快照 **{bio_then}** → 現行 **{bio_now}**。", "",
         "> 兩者不是同一件事。前者是「2019 年 COSING 這樣標」，"
         "後者是「現行法規今天這樣管」。合併使用會把兩個時點混為一談。", "",
         "## 二、現行法規下，生物來源萃取物涉及最多的條文", "",
         "| 條文 | 內容 | 萃取物數 | 科數 |", "| --- | --- | --- | --- |"]
    L += [f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} |" for r in top]

    L += ["", "## 三、2019 之後才被納管的萃取物（依科）", "",
          "這些成分在我們的 2019 快照中沒有任何限制標記，"
          "但現行 Annex 條文已將其列入。", "",
          "| 科 | 新增受限數 |", "| --- | --- |"]
    L += [f"| {r[0] or '(未定)'} | {r[1]} |" for r in newly]
    L += ["", f"反向：2019 有標記但不在現行條文適用清單中者 **{gone}** 筆"
          "（可能為條文改號、除名，或現行條文未逐一列出成分）。", ""]

    L += ["", "## 四、各科在現行法規下的受限情形", "",
          "| 科 | 受限萃取物數 |", "| --- | --- |"]
    L += [f"| {r[0]} | {r[1]} |" for r in fam]

    L += ["", "## 五、查詢方式", "",
          "已建立 view `extract_regulation`，一次接起萃取物、分類階層、部位製程與法規條文：", "",
          "```sql", "SELECT inci_name, family_final, plant_part,",
          "       annex_no || '/' || annex_ref AS 條文,",
          "       regulated_substance, max_concentration, product_type",
          "FROM extract_regulation",
          "WHERE source = 'annex_2026' AND family_final = 'Rutaceae'", "```", "",
          "## 六、未解析的 restriction 文字", "",
          f"{n_unparsed} 筆 `restriction` 不含任何 Annex 引用"
          "（如 `Suspected carcinogen based on ECHA`、"
          "`Reported Functions as Fragrance Ingredients`）。"
          "這些**沒有被丟棄**，存於 `restriction_unparsed` 表。", "",
          f"另有 {n_cmr} 筆文字中提到 CMR 分類（致癌／致突變／生殖毒性），"
          "存於 `ingredient_cmr` 表。", ""]

    checks = [
        ("regulation 表已載入", n_reg > 2000),
        ("2019 引用解析率 > 80%", resolved / n19 > 0.80),
        ("兩條連結路徑都有資料", n19 > 0 and n26 > 0),
        ("未解析文字有保留，未丟棄",
         q("SELECT count(*) FROM restriction_unparsed")[0][0] == n_unparsed),
        ("view extract_regulation 可查詢",
         q("SELECT count(*) FROM extract_regulation")[0][0] > 0),
    ]
    L += ["## 七、驗收檢查", "", "| 檢查項 | 結果 |", "| --- | --- |"]
    L += [f"| {lab} | {'✅ 通過' if ok else '❌ 失敗'} |" for lab, ok in checks]
    print("\n驗收：")
    for lab, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {lab}")

    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "regulation-report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {REPORTS / 'regulation-report.md'}")


if __name__ == "__main__":
    main()
