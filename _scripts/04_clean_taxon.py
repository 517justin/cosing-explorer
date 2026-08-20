"""Phase 1c - normalise family names and build the final `extract` table.

Two corrections are applied in order:

  1. family_typo.csv - misspellings ('Laminaceae' -> 'Lamiaceae')
  2. family_apg.csv  - valid but superseded names ('Compositae' -> 'Asteraceae')

Order matters. 'Palmaceae' is not a validly published name at all, so it is a
typo and goes through step 1 straight to Arecaceae; 'Palmae' is a legitimate
conserved alternative and goes through step 2. Both converge on one node.

Families listed in split_families.csv are deliberately NOT mapped here. APG IV
broke them up, so the right family depends on the genus and only a GBIF lookup
(04_gbif.py) can decide. They are flagged `needs_gbif` and left raw.
"""

import csv

from common import CORRECTIONS, REPORTS, SUFFIX, T, conflicts_file, connect


def main():
    con = connect()

    typo = {r["raw"]: r for r in _read("family_typo.csv")}
    apg = {r["raw"]: r for r in _read("family_apg.csv")}
    split = {r["raw"]: r for r in _read("split_families.csv")}
    conflicts = {
        int(r["ref_no"]): r
        for r in _read(conflicts_file())
        if r["resolution"] and r["resolution"] != "auto"
    }

    rows = con.execute(
        f"""
        SELECT ref_no, family_raw, genus_raw, species_raw, binomial_raw,
               taxon_source, taxon_status, typo_applied
        FROM {T('extract_parsed')} ORDER BY ref_no
        """
    ).fetchall()

    out = []
    for (ref_no, fam_raw, genus, species, binom, src, status, typo_flag) in rows:
        fam, steps = fam_raw, []

        if fam in typo:
            steps.append(f"typo:{fam}->{typo[fam]['corrected']}")
            fam = typo[fam]["corrected"]
        if fam in apg:
            steps.append(f"nomenclature:{fam}->{apg[fam]['accepted']}")
            fam = apg[fam]["accepted"]

        needs_gbif = fam in split
        if needs_gbif:
            steps.append(f"needs_gbif:{fam} was split in APG IV")

        # A decision in conflicts.csv (human or GBIF) overrides the parser.
        decided = conflicts.get(ref_no)
        if decided:
            if decided["resolution"] == "excluded":
                # INCI and the description name two different species and no
                # external source can say which was meant. The ingredient stays
                # in `ingredient`; it just never joins the taxonomic graph.
                genus = species = binom = None
                src = decided["resolution"]
                status = "excluded"
            elif decided["resolved_to"]:
                parts = decided["resolved_to"].split()
                if len(parts) == 2:
                    genus, species = parts
                    binom = decided["resolved_to"]
                    src = decided["resolution"]
                    status = f"resolved_by_{decided['resolution']}"

        out.append(
            {
                "ref_no": ref_no,
                "family_raw": fam_raw,
                "family_accepted": None if needs_gbif else fam,
                "family_needs_gbif": needs_gbif,
                "family_correction": "; ".join(steps) or None,
                "genus_raw": genus,
                "species_raw": species,
                "binomial_raw": binom,
                "taxon_source": src,
                "taxon_status": status,
                "typo_applied": typo_flag,
                "is_resolved": bool(genus) and not needs_gbif,
            }
        )

    con.execute(f"DROP TABLE IF EXISTS {T('extract')}")
    con.execute(
        f"""
        CREATE TABLE {T('extract')} (
            ref_no             INTEGER PRIMARY KEY,
            family_raw         VARCHAR,
            family_accepted    VARCHAR,
            family_needs_gbif  BOOLEAN,
            family_correction  VARCHAR,
            genus_raw          VARCHAR,
            species_raw        VARCHAR,
            binomial_raw       VARCHAR,
            taxon_source       VARCHAR,
            taxon_status       VARCHAR,
            typo_applied       BOOLEAN,
            is_resolved        BOOLEAN
        )
        """
    )
    cols = list(out[0])
    con.executemany(
        f"INSERT INTO {T('extract')} VALUES ({','.join(['?'] * len(cols))})",
        [[r[c] for c in cols] for r in out],
    )

    _report(con, out)
    con.close()


def _report(con, out):
    q = lambda s: con.execute(s).fetchall()
    n = len(out)
    raw_fams = len({r["family_raw"] for r in out})
    acc_fams = len({r["family_accepted"] for r in out if r["family_accepted"]})
    corrected = sum(1 for r in out if r["family_correction"])
    pending = sum(1 for r in out if r["family_needs_gbif"])

    print(f"extract rows            : {n}")
    print(f"  distinct family_raw   : {raw_fams}")
    print(f"  distinct family_accept: {acc_fams}")
    print(f"  rows family-corrected : {corrected}")
    print(f"  rows awaiting GBIF    : {pending}")

    REPORTS.mkdir(exist_ok=True)
    lines = [
        f"# Phase 1 清理報告{' — 2026 全庫' if SUFFIX else ''}",
        "",
        f"- 生物來源列：**{n}**",
        f"- 科名寫法（原始）：**{raw_fams}** 種",
        f"- 科名寫法（正規化後）：**{acc_fams}** 種",
        f"- 經過科名修正的列：**{corrected}**",
        f"- 待 GBIF 判定（APG IV 拆分科）：**{pending}**",
        "",
        "## 科名正規化的合併效果",
        "",
        "| family_raw | family_accepted | 列數 | 修正類型 |",
        "| --- | --- | --- | --- |",
    ]
    for r in q(
        f"""
        SELECT family_raw, coalesce(family_accepted,'(待 GBIF)'), count(*), family_correction
        FROM {T('extract')} WHERE family_correction IS NOT NULL
        GROUP BY 1,2,4 ORDER BY 3 DESC
        """
    ):
        kind = "typo" if r[3].startswith("typo") else (
            "needs_gbif" if r[3].startswith("needs_gbif") else "nomenclature")
        lines += [f"| {r[0]} | {r[1]} | {r[2]} | {kind} |"]

    lines += ["", "## 解析狀態分布", "", "| taxon_status | 列數 |", "| --- | --- |"]
    for r in q(f"SELECT taxon_status, count(*) FROM {T('extract')} GROUP BY 1 ORDER BY 2 DESC"):
        lines += [f"| {r[0]} | {r[1]} |"]

    gb = q(f"SELECT ref_no, binomial_raw FROM {T('extract')} "
           "WHERE taxon_status='resolved_by_gbif' ORDER BY 1")
    if gb:
        lines += ["", "## 經 GBIF 查證後更正", "",
                  "INCI 與敘述的兩個名稱在 GBIF 骨幹中指向同一個接受名，"
                  "屬同物異名，已更正為接受名。", "",
                  "| ref_no | 更正為 |", "| --- | --- |"]
        lines += [f"| {r[0]} | {r[1]} |" for r in gb]

    ex = q(f"SELECT e.ref_no, i.inci_name FROM {T('extract')} e "
           f"JOIN {T('ingredient')} i USING(ref_no) "
           "WHERE e.taxon_status='excluded' ORDER BY 1")
    if ex:
        lines += ["", "## 查無定論，未納入圖譜", "",
                  "INCI 名稱與敘述指向**兩個不同的接受種**，GBIF 無法判斷原意為何。"
                  "這些成分仍留在 `ingredient` 主表，但不建立物種／屬／科連結，"
                  "因此不會污染分類階層。", "",
                  "| ref_no | INCI 名稱 |", "| --- | --- |"]
        lines += [f"| {r[0]} | {r[1]} |" for r in ex]

    lines += [
        "",
        "## 驗收檢查",
        "",
        "| 檢查項 | 結果 |",
        "| --- | --- |",
    ]
    checks = [
        (f"{T('ingredient')} 有資料",
         q(f"SELECT count(*) FROM {T('ingredient')}")[0][0] > 0),
        ("Palmae/Palmaceae/Arecaceae 合併為單一科",
         len({r[0] for r in q(
             f"SELECT family_accepted FROM {T('extract')} WHERE family_raw IN "
             "('Palmae','Palmaceae','Arecaceae')")}) == 1),
        ("Laminaceae -> Lamiaceae",
         (q(f"SELECT DISTINCT family_accepted FROM {T('extract')} "
             "WHERE family_raw='Laminaceae'") or [["Lamiaceae"]])[0][0] == "Lamiaceae"),
        ("屬名解析率 > 98%",
         q(f"SELECT count(*) FILTER (WHERE genus_raw IS NOT NULL)*1.0/count(*) FROM {T('extract')}")
         [0][0] > 0.98),
        ("Liliaceae / Scrophulariaceae 未被科層級硬映射",
         all(r[0] for r in q(
             f"SELECT family_needs_gbif FROM {T('extract')} WHERE family_raw IN "
             "('Liliaceae','Scrophulariaceae')"))),
        ("查無定論者未帶入物種連結",
         q(f"SELECT count(*) FROM {T('extract')} WHERE taxon_status='excluded' "
           "AND (genus_raw IS NOT NULL OR species_raw IS NOT NULL)")[0][0] == 0),
        ("conflicts.csv 無未裁決項目",
         q(f"SELECT count(*) FROM {T('extract')} WHERE taxon_status IN "
           "('species_mismatch','genus_mismatch','unparseable')")[0][0] == 0),
    ]
    for label, ok in checks:
        lines += [f"| {label} | {'✅ 通過' if ok else '❌ 失敗'} |"]

    (REPORTS / f"cleaning-report{SUFFIX}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n驗收：")
    for label, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}")
    print(f"\nwrote {REPORTS / ('cleaning-report' + SUFFIX + '.md')}")


def _read(name):
    path = CORRECTIONS / name
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    main()
