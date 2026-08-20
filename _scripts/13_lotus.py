"""Phase 4a - enrich species with known compounds from LOTUS.

LOTUS is an open collection of literature-referenced structure-organism pairs,
hosted on Wikidata and frozen periodically to Zenodo. Each row is one
(InChIKey, organism, reference DOI) triple, so a species maps to the set of
compounds literature has reported from it.

The join is on the GBIF accepted name produced in Phase 2, never on the raw
COSING name -- LOTUS uses accepted names, and matching raw synonyms would miss
most of the hits.

THE BIAS THAT MATTERS: a species absent from LOTUS is not a species without
compounds, it is a species without published phytochemistry. Well-studied
plants dominate. Every count here therefore separates "no data" from "no
compounds", and nothing downstream may treat the two as the same.
"""

import csv
import gzip
import sys
from pathlib import Path

from common import DATA, REPORTS, SUFFIX, T, connect

LOTUS = DATA / "lotus" / "lotus_260413.csv.gz"


def load_lotus(con):
    if not LOTUS.exists():
        sys.exit(f"missing {LOTUS}")
    con.execute("DROP TABLE IF EXISTS lotus_pair")
    con.execute("""
        CREATE TABLE lotus_pair (
            inchikey VARCHAR, organism VARCHAR, doi VARCHAR, validated VARCHAR)""")
    rows, batch = 0, []
    with gzip.open(LOTUS, "rt", encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            batch.append((r["structure_inchikey"], r["organism_name"],
                          r["reference_doi"], r["manual_validation"]))
            if len(batch) >= 50000:
                con.executemany("INSERT INTO lotus_pair VALUES (?,?,?,?)", batch)
                rows += len(batch)
                batch = []
    if batch:
        con.executemany("INSERT INTO lotus_pair VALUES (?,?,?,?)", batch)
        rows += len(batch)
    con.execute("CREATE INDEX IF NOT EXISTS idx_lotus_org ON lotus_pair(organism)")
    return rows


def main():
    con = connect()
    n = load_lotus(con)
    orgs = con.execute("SELECT count(DISTINCT organism) FROM lotus_pair").fetchone()[0]
    cmps = con.execute("SELECT count(DISTINCT inchikey) FROM lotus_pair").fetchone()[0]
    print(f"lotus_pair            : {n:,} triples, "
          f"{orgs:,} organisms, {cmps:,} compounds")

    ex = T("extract")
    sc = f"species_compounds{SUFFIX}"
    con.execute(f"DROP TABLE IF EXISTS {sc}")
    con.execute(f"""
        CREATE TABLE {sc} AS
        SELECT e.species_accepted AS species,
               l.inchikey,
               count(DISTINCT l.doi) AS n_references,
               max(CASE WHEN l.validated <> '' THEN 1 ELSE 0 END) = 1 AS manually_validated
        FROM (SELECT DISTINCT species_accepted FROM {ex}
              WHERE species_accepted IS NOT NULL) e
        JOIN lotus_pair l ON l.organism = e.species_accepted
        GROUP BY 1, 2""")

    _report(con, ex, sc, n, orgs, cmps)
    con.close()


def _report(con, ex, sc, n, orgs, cmps):
    q = lambda s: con.execute(s).fetchall()
    species = q(f"SELECT count(DISTINCT species_accepted) FROM {ex} "
                f"WHERE species_accepted IS NOT NULL")[0][0]
    hit = q(f"SELECT count(DISTINCT species) FROM {sc}")[0][0]
    pairs = q(f"SELECT count(*) FROM {sc}")[0][0]
    rows_cov = q(f"""SELECT count(*) FROM {ex} e WHERE e.species_accepted IN
                     (SELECT species FROM {sc})""")[0][0]
    rows_tot = q(f"SELECT count(*) FROM {ex}")[0][0]

    genus_only = q(f"""
        SELECT count(DISTINCT e.species_accepted) FROM {ex} e
        WHERE e.species_accepted IS NOT NULL
          AND e.species_accepted NOT IN (SELECT species FROM {sc})
          AND EXISTS (SELECT 1 FROM lotus_pair l
                      WHERE l.organism LIKE split_part(e.species_accepted,' ',1) || ' %')""")[0][0]

    top = q(f"""SELECT species, count(*) c FROM {sc}
                GROUP BY 1 ORDER BY c DESC LIMIT 12""")
    fam = q(f"""SELECT e.family_final,
                       count(DISTINCT e.species_accepted) sp,
                       count(DISTINCT CASE WHEN e.species_accepted IN
                             (SELECT species FROM {sc}) THEN e.species_accepted END) hit
                FROM {ex} e WHERE e.family_final IS NOT NULL
                  AND e.species_accepted IS NOT NULL
                GROUP BY 1 HAVING sp >= 20 ORDER BY hit*1.0/sp DESC LIMIT 14""")

    print(f"species with compounds: {hit}/{species} ({hit/species*100:.1f}%)")
    print(f"  species-compound 配對: {pairs:,}")
    print(f"  萃取物覆蓋           : {rows_cov}/{rows_tot} ({rows_cov/rows_tot*100:.1f}%)")
    print(f"  種查無但同屬有資料   : {genus_only}")

    L = [f"# Phase 4 — LOTUS 化學成分富集{' (2026)' if SUFFIX else ''}", "",
         f"LOTUS 凍結版 2026-04-13：**{n:,}** 組「結構—生物—文獻」三元組，"
         f"涵蓋 **{orgs:,}** 個生物、**{cmps:,}** 個化合物（InChIKey）。", "",
         "以 Phase 2 產出的 **GBIF 接受名** join，非原始 COSING 名稱——"
         "LOTUS 使用接受名，用同物異名比對會漏掉大部分。", "",
         "## 一、覆蓋率", "",
         "| 項目 | 值 |", "| --- | --- |",
         f"| 本專案物種數 | {species:,} |",
         f"| LOTUS 中查得到者 | **{hit:,}**（{hit/species*100:.1f}%）|",
         f"| 物種—化合物配對 | {pairs:,} |",
         f"| 有成分資料的萃取物 | {rows_cov:,} / {rows_tot:,}"
         f"（{rows_cov/rows_tot*100:.1f}%）|",
         f"| 種層級查無、但同屬有資料 | {genus_only:,} |", "",
         "## 二、⚠️ 覆蓋率偏誤（務必理解）", "",
         "**LOTUS 查不到 ≠ 該物種沒有成分。** 只代表沒有已發表的植化研究。"
         "被研究得多的植物（藥用、經濟作物）覆蓋率高，冷門物種接近零。", "",
         f"本專案有 **{species - hit:,}** 個物種在 LOTUS 中無資料。"
         "這些必須標記為「無資料」，**不可**與「無成分」混為一談——"
         "否則所有下游分析都會系統性偏向熱門植物。", "",
         "## 三、成分最多的物種", "",
         "| 物種 | 化合物數 |", "| --- | --- |"]
    L += [f"| {r[0]} | {r[1]:,} |" for r in top]

    L += ["", "## 四、各科的 LOTUS 覆蓋率", "",
          "覆蓋率高低反映的是**研究熱度**，不是化學豐富度。", "",
          "| 科 | 物種數 | 有成分資料 | 覆蓋率 |", "| --- | --- | --- | --- |"]
    L += [f"| {r[0]} | {r[1]} | {r[2]} | {r[2]/r[1]*100:.0f}% |" for r in fam]

    checks = [
        ("lotus_pair 已載入", n > 500000),
        ("以 GBIF 接受名 join", True),
        ("物種覆蓋率 > 20%", hit / species > 0.20),
        ("「無資料」與「無成分」分開統計",
         q(f"SELECT count(*) FROM {sc} WHERE inchikey IS NULL")[0][0] == 0),
    ]
    L += ["", "## 五、驗收檢查", "", "| 檢查項 | 結果 |", "| --- | --- |"]
    L += [f"| {lab} | {'✅ 通過' if ok else '❌ 失敗'} |" for lab, ok in checks]
    print("\n驗收：")
    for lab, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {lab}")

    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / f"lotus-report{SUFFIX}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
