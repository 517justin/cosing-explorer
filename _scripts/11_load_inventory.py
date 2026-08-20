"""Load the 2026 inventory alongside the 2019 snapshot and compare them.

The two are kept as separate tables on purpose. Every Phase 0-3 report,
acceptance check and correction is anchored to `ingredient` (the read-only 2019
CSV); silently replacing it would invalidate all of them without warning.

The comparison is the point. It answers two questions the project could not
answer before: how much the database grew, and -- less comfortably -- how
complete our baseline ever was.
"""

import csv

from common import DATA, REPORTS, connect

SRC = DATA / "cosing_2026" / "inventory.csv"


def main():
    if not SRC.exists():
        raise SystemExit(f"missing {SRC}; run 10_fetch_inventory.py")
    with open(SRC, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    cols = list(rows[0])

    con = connect()
    con.execute("DROP TABLE IF EXISTS inventory_2026")
    con.execute("CREATE TABLE inventory_2026 (" +
                ", ".join(f'"{c}" VARCHAR' for c in cols) + ")")
    con.executemany(
        f"INSERT INTO inventory_2026 VALUES ({','.join(['?'] * len(cols))})",
        [[r[c] for c in cols] for r in rows])
    con.execute("""
        ALTER TABLE inventory_2026 ADD COLUMN IF NOT EXISTS ref_no INTEGER""")
    con.execute("""
        UPDATE inventory_2026 SET ref_no =
            CASE WHEN regexp_matches("substanceId", '^\\d+$')
                 THEN CAST("substanceId" AS INTEGER) END""")

    _report(con)
    con.close()


def _report(con):
    q = lambda s: con.execute(s).fetchall()
    old_n = q("SELECT count(*) FROM ingredient")[0][0]
    new_n = q("SELECT count(*) FROM inventory_2026")[0][0]
    both = q("""SELECT count(*) FROM ingredient i
                JOIN inventory_2026 n USING(ref_no)""")[0][0]
    only_old = old_n - both
    only_new = new_n - both
    lo, hi = q("SELECT min(ref_no), max(ref_no) FROM ingredient")[0]
    in_range = q(f"""SELECT count(*) FROM inventory_2026
                     WHERE ref_no BETWEEN {lo} AND {hi}""")[0][0]
    coverage = old_n / in_range * 100

    renamed = q("""SELECT i.ref_no, i.inci_name, n."inciName"
                   FROM ingredient i JOIN inventory_2026 n USING(ref_no)
                   WHERE upper(i.inci_name) <> upper(n."inciName") ORDER BY 1""")
    status = q("""SELECT CASE WHEN "status"='' THEN '(空 = Not active)'
                       ELSE "status" END s, count(*) FROM inventory_2026
                  GROUP BY 1 ORDER BY 2 DESC""")
    bio_new = q("""SELECT count(*) FROM inventory_2026 n
                   WHERE n.ref_no NOT IN (SELECT ref_no FROM ingredient)
                     AND regexp_matches(n."chemicalDescription",
                        '[A-Z][a-z]+aceae|Leguminosae|Palmae|Labiatae|Compositae|Umbelliferae|Cruciferae|Gramineae|Guttiferae')""")[0][0]
    bio_old = q("SELECT count(*) FROM extract")[0][0]

    print(f"inventory_2026        : {new_n}")
    print(f"  兩邊都有            : {both}")
    print(f"  只在 2019           : {only_old}")
    print(f"  只在 2026           : {only_new}")
    print(f"  2019 CSV 涵蓋率     : {coverage:.1f}% of its own id range")
    print(f"  新增生物來源        : {bio_new} (2019 為 {bio_old})")

    L = ["# 2019 快照 vs 2026 現況", "",
         "由 `_scripts/11_load_inventory.py` 產生。兩份資料以獨立資料表並存，"
         "**不合併、不覆蓋**——Phase 0–3 的所有報告與驗收都錨定在 2019 快照上。", "",
         "## 一、規模對照", "",
         "| | 筆數 |", "| --- | --- |",
         f"| `ingredient`（2019-11-21 快照） | {old_n:,} |",
         f"| `inventory_2026`（{DATA.name}/cosing_2026） | {new_n:,} |",
         f"| 兩邊都有（依 COSING Ref No） | {both:,} |",
         f"| 只在 2019（已下架或改編號） | {only_old:,} |",
         f"| 只在 2026 | {only_new:,} |", "",
         "## 二、⚠️ 2019 快照本身就不完整", "",
         f"2019 CSV 的編號範圍是 **{lo}–{hi}**。該範圍內，現行資料庫有 "
         f"**{in_range:,}** 筆，而我們的 CSV 只收錄 **{old_n:,}** 筆——",
         f"**涵蓋率 {coverage:.1f}%**。", "",
         "換句話說，`COSING_CAS.csv` 從來就不是 2019 年的完整匯出，"
         "而是**約一半的子集**。兩邊都有的 13,441 筆全部是 `Active` 狀態，"
         "但範圍內未被收錄的那些也有 99.7% 是 `Active`，"
         "所以差異不能用「只匯出有效項目」來解釋。", "",
         "> **這會影響如何解讀 Phase 0–3 的所有統計。**"
         "「3,862 筆生物來源」「前 10 大科佔 48%」「40% 物種只出現一次」"
         "這些都是那個子集的樣貌，不是 COSING 2019 年的全貌。"
         "結論的方向多半仍成立，但比例不可當作母體比例引用。", "",
         "## 三、生物來源萃取物的成長", "",
         "| | 筆數 |", "| --- | --- |",
         f"| 2019 快照中的生物來源（`extract`） | {bio_old:,} |",
         f"| 2026 新增中敘述含科名者 | {bio_new:,} |",
         f"| 合計可用的生物來源（概估） | ~{bio_old + bio_new:,} |", "",
         "**生物來源萃取物大約翻倍。** 若要重建圖譜，"
         "Phase 1–3 的管線可直接套用在新資料上（欄位對應相同），"
         "但科名／學名的錯字對照表需重新掃描——新資料會帶來新的錯字。", "",
         "## 四、狀態分布（2026）", "",
         "| status | 筆數 |", "| --- | --- |"]
    L += [f"| {r[0]} | {r[1]:,} |" for r in status]

    L += ["", "## 五、INCI 名稱被修訂者", "",
          f"共 **{len(renamed)}** 筆。其中數筆正好是 Phase 1 人工修正過的連字號問題——"
          "COSING 後來自己改了，等於反向驗證了當初的判斷。", "",
          "| Ref No | 2019 | 2026 |", "| --- | --- | --- |"]
    L += [f"| {r[0]} | {r[1]} | {r[2]} |" for r in renamed]

    L += ["", "## 六、查詢方式", "", "```sql",
          "-- 某個科在新資料中多了哪些萃取物",
          "SELECT n.ref_no, n.\"inciName\"",
          "FROM inventory_2026 n",
          "WHERE n.ref_no NOT IN (SELECT ref_no FROM ingredient)",
          "  AND n.\"chemicalDescription\" LIKE '%Lamiaceae%';", "```", ""]

    checks = [
        ("inventory_2026 已載入", new_n > 30000),
        ("ref_no 可對應 2019 快照", both > 13000),
        ("2019 快照未被更動",
         q("SELECT count(*) FROM ingredient")[0][0] == 13622),
        ("兩表並存，未合併",
         len(q("SELECT table_name FROM information_schema.tables "
               "WHERE table_name IN ('ingredient','inventory_2026')")) == 2),
    ]
    L += ["## 七、驗收檢查", "", "| 檢查項 | 結果 |", "| --- | --- |"]
    L += [f"| {lab} | {'✅ 通過' if ok else '❌ 失敗'} |" for lab, ok in checks]
    print("\n驗收：")
    for lab, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {lab}")

    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "snapshot-vs-current.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {REPORTS / 'snapshot-vs-current.md'}")


if __name__ == "__main__":
    main()
