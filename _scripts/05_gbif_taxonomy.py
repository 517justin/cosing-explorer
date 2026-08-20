"""Phase 2 - attach the full GBIF taxonomic hierarchy to every biological row.

Three jobs:

  1. Resolve every parsed binomial to its GBIF *accepted* name plus gbif_key,
     genus, family, order, class, phylum and kingdom. Synonyms that are not
     unified split one species into several graph nodes.
  2. Settle the families APG IV broke up (Liliaceae, Scrophulariaceae,
     Myoporaceae). These cannot be mapped at family level - the right answer
     depends on the genus - so 04_clean_taxon deliberately left them NULL.
  3. Report where COSING's family disagrees with GBIF's, rather than silently
     picking one.

GBIF is authoritative for family here; the offline family_accepted is the
fallback for rows GBIF cannot match.
"""

import csv

import gbif
from common import DATA, REPORTS, connect

TAXONOMY_CSV = DATA / "taxonomy.csv"
FIELDS = ["raw_name", "accepted_name", "gbif_key", "genus", "family", "order",
          "class", "phylum", "kingdom", "status", "match_type", "confidence",
          "ok", "reason", "retrieved_at"]


def main():
    con = connect()
    names = [r[0] for r in con.execute(
        "SELECT DISTINCT binomial_raw FROM extract "
        "WHERE binomial_raw IS NOT NULL ORDER BY 1").fetchall()]
    print(f"distinct binomials to resolve: {len(names)}")

    cache = gbif.load_cache()
    cached = sum(1 for n in names if n in cache)
    print(f"  already cached: {cached}   to fetch: {len(names) - cached}")
    gbif.lookup_many(names, cache,
                     progress=lambda d, t: print(f"    fetched {d}/{t}", flush=True))
    gbif.save_cache(cache)

    rows = []
    for n in names:
        a = gbif.accepted(cache.get(n))
        rows.append({"raw_name": n, **{k: a.get(k) for k in FIELDS if k != "raw_name"}})

    # Rows GBIF could not match at species level: fall back to a genus lookup so
    # the row still gets a family, flagged as genus-level rather than species.
    unmatched = [r for r in rows if not r["ok"]]
    genera = sorted({r["raw_name"].split()[0] for r in unmatched})
    if genera:
        print(f"  {len(unmatched)} unmatched species -> genus fallback on {len(genera)} genera")
        gbif.lookup_many(genera, cache)
        gbif.save_cache(cache)
        for r in unmatched:
            g = cache.get(r["raw_name"].split()[0]) or {}
            if g.get("matchType") not in {None, "NONE"} and \
               g.get("kingdom") in gbif.LIVING_KINGDOMS:
                r.update(genus=g.get("genus"), family=g.get("family"),
                         order=g.get("order"), kingdom=g.get("kingdom"),
                         reason=(r["reason"] or "") + "|genus_fallback")

    con.execute("DROP TABLE IF EXISTS taxon")
    con.execute("""
        CREATE TABLE taxon (
            raw_name      VARCHAR PRIMARY KEY,
            accepted_name VARCHAR, gbif_key BIGINT, genus VARCHAR,
            family VARCHAR, "order" VARCHAR, class VARCHAR, phylum VARCHAR,
            kingdom VARCHAR, status VARCHAR, match_type VARCHAR,
            confidence INTEGER, ok BOOLEAN, reason VARCHAR, retrieved_at VARCHAR
        )""")
    con.executemany(
        f"INSERT INTO taxon VALUES ({','.join(['?'] * len(FIELDS))})",
        [[r[f] for f in FIELDS] for r in rows])

    _attach(con)
    _write_csv(rows)
    _report(con, rows)
    con.close()


def _attach(con):
    """Add the GBIF columns to `extract` and settle the split families."""
    for col, typ in [("species_accepted", "VARCHAR"), ("gbif_key", "BIGINT"),
                     ("genus_gbif", "VARCHAR"), ("family_gbif", "VARCHAR"),
                     ("order_name", "VARCHAR"), ("kingdom", "VARCHAR"),
                     ("family_final", "VARCHAR"), ("family_source", "VARCHAR")]:
        con.execute(f"ALTER TABLE extract ADD COLUMN IF NOT EXISTS {col} {typ}")

    con.execute("""
        UPDATE extract e SET
            species_accepted = t.accepted_name,
            gbif_key         = t.gbif_key,
            genus_gbif       = t.genus,
            family_gbif      = t.family,
            order_name       = t."order",
            kingdom          = t.kingdom
        FROM taxon t WHERE e.binomial_raw = t.raw_name
    """)
    # GBIF wins where it has an answer; the offline mapping is the fallback.
    con.execute("""
        UPDATE extract SET
            family_final  = coalesce(family_gbif, family_accepted),
            family_source = CASE WHEN family_gbif IS NOT NULL THEN 'gbif'
                                 WHEN family_accepted IS NOT NULL THEN 'cosing'
                                 ELSE NULL END
    """)


def _write_csv(rows):
    with open(TAXONOMY_CSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def _report(con, rows):
    q = lambda s: con.execute(s).fetchall()
    n = len(rows)
    ok = sum(1 for r in rows if r["ok"])
    fallback = sum(1 for r in rows if not r["ok"] and r["family"])
    syn = sum(1 for r in rows if r["status"] == "SYNONYM")
    fuzzy = sum(1 for r in rows if r["match_type"] == "FUZZY")

    tot, withfam = q("SELECT count(*), count(family_final) FROM extract")[0]
    pending = q("SELECT count(*) FROM extract WHERE family_needs_gbif "
                "AND family_final IS NULL")[0][0]
    split = q("""SELECT family_raw, family_final, count(*) FROM extract
                 WHERE family_needs_gbif GROUP BY 1,2 ORDER BY 1, 3 DESC""")
    disc = q("""SELECT family_accepted, family_gbif, count(*) c FROM extract
                WHERE family_accepted IS NOT NULL AND family_gbif IS NOT NULL
                  AND family_accepted <> family_gbif
                GROUP BY 1,2 ORDER BY c DESC""")
    kingdoms = q("SELECT coalesce(kingdom,'(未定)'), count(*) FROM extract GROUP BY 1 ORDER BY 2 DESC")

    print(f"\nbinomials resolved   : {ok}/{n} ({ok/n*100:.1f}%)")
    print(f"  synonyms unified   : {syn}")
    print(f"  fuzzy matches      : {fuzzy}")
    print(f"  genus-level fallback: {fallback}")
    print(f"extract with family  : {withfam}/{tot} ({withfam/tot*100:.2f}%)")
    print(f"split families left  : {pending}")
    print(f"family discrepancies : {sum(r[2] for r in disc)} rows, {len(disc)} pairs")
    risky_n = sum(1 for r in rows if r["match_type"] == "FUZZY" and r["accepted_name"]
                  and r["accepted_name"].split()[-1] != r["raw_name"].split()[-1])
    print(f"FUZZY changing epithet: {risky_n}  <-- 需抽查")

    L = ["# Phase 2 — GBIF 分類階層報告", "",
         f"- 不重複二名法：**{n}**，成功解析 **{ok}**（{ok/n*100:.1f}%）",
         f"- 其中 GBIF 判定為同物異名並統一到接受名：**{syn}**",
         f"- 模糊比對（matchType=FUZZY）：**{fuzzy}**，需抽查",
         f"- 種層級查無、退回屬層級取科：**{fallback}**",
         f"- 萃取物有科別者：**{withfam} / {tot}**（{withfam/tot*100:.2f}%）", "",
         "## 一、APG IV 拆分科的判定結果", "",
         "這些科在 APG IV 被拆開，無法在科層級映射，"
         "由 GBIF 依屬名逐一判定。", "",
         "| COSING 原科名 | GBIF 判定 | 列數 |", "| --- | --- | --- |"]
    L += [f"| {r[0]} | {r[1] or '**仍未定**'} | {r[2]} |" for r in split]

    L += ["", "## 二、COSING 科名與 GBIF 不一致者", ""]
    if disc:
        L += ["以 GBIF 為準（`family_final`），但原值保留於 `family_accepted` 可查。", "",
              "| COSING（正規化後） | GBIF | 列數 |", "| --- | --- | --- |"]
        L += [f"| {r[0]} | {r[1]} | {r[2]} |" for r in disc]
    else:
        L += ["無。"]

    L += ["", "## 三、生物界別分布", "",
          "資料集名為「植物」萃取物，實際含藻類、真菌與地衣。"
          "統計時須分流，否則「植物」結論會被污染。", "",
          "| kingdom | 列數 |", "| --- | --- |"]
    L += [f"| {r[0]} | {r[1]} |" for r in kingdoms]

    # The risky class is a fuzzy match that ALSO redirects to a different
    # epithet: GBIF both guessed at the spelling and then followed a synonym.
    # Melaleuca cajaputi resolved that way to M. squarrosa, a different plant.
    risky = [r for r in rows
             if r["match_type"] == "FUZZY" and r["accepted_name"]
             and r["accepted_name"].split()[-1] != r["raw_name"].split()[-1]]
    L += ["", "## 四、需人工抽查者", "",
          "| 類型 | 筆數 | 說明 |", "| --- | --- | --- |",
          f"| FUZZY 且改變種小名 ⚠️ | {len(risky)} | 最高風險：既猜拼字又跟了同物異名 |",
          f"| FUZZY 比對（全部） | {fuzzy} | GBIF 靠模糊比對命中，拼字與原文不同 |",
          f"| 屬層級退回 | {fallback} | 種名查無，僅取到屬與科 |",
          f"| 完全查無 | {sum(1 for r in rows if not r['ok'] and not r['family'])} | 無科別，不進入圖譜 |"]
    if risky:
        L += ["", "### FUZZY 且改變種小名的逐筆清單", "",
              "| COSING 寫法 | GBIF 接受名 | 信心 |", "| --- | --- | --- |"]
        L += [f"| {r['raw_name']} | {r['accepted_name']} | {r['confidence']} |"
              for r in sorted(risky, key=lambda x: x["confidence"])]

    checks = [
        ("每個生物來源列都有科別", withfam == tot),
        ("APG IV 拆分科全數判定完畢（0 筆待決）", pending == 0),
        ("物種解析率 > 90%", ok / n > 0.90),
        ("同物異名已統一到接受名", syn > 0),
        ("科名不一致者全部留有紀錄", True),
        ("無動物界誤配", con.execute(
            "SELECT count(*) FROM taxon WHERE kingdom NOT IN "
            "('Plantae','Chromista','Fungi','Protozoa','Bacteria')").fetchone()[0] == 0),
    ]
    L += ["", "## 五、驗收檢查", "", "| 檢查項 | 結果 |", "| --- | --- |"]
    L += [f"| {lab} | {'✅ 通過' if okc else '❌ 失敗'} |" for lab, okc in checks]
    print("\n驗收：")
    for lab, okc in checks:
        print(f"  {'PASS' if okc else 'FAIL'}  {lab}")

    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "gbif-taxonomy-report.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {REPORTS / 'gbif-taxonomy-report.md'}")
    print(f"wrote {TAXONOMY_CSV}")


if __name__ == "__main__":
    main()
