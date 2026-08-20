"""Phase 3 - extract plant part, process and process modifiers.

Pure dictionary matching, no LLM. In INCI naming the part and the product form
ARE tokens of the name ('PINUS PINASTER SEED OIL'), so a controlled vocabulary
is both sufficient and reproducible.

Two passes for the part:
  1. tokens of the INCI name, minus the binomial (which 02 already identified)
  2. the description, for the ~790 rows whose INCI name names no part
     ('Acacia Decurrens Extract is an extract of the sprouts of the acacia...')

Rows where neither pass finds anything are left NULL. An unstated part is not
the same as a whole-plant extract, and guessing would quietly merge materials
whose composition differs completely.
"""

import csv
import re
from collections import Counter

from common import DATA, REPORTS, SUFFIX, T, connect

VOCAB = DATA / "vocab"


def load(name, key):
    with open(VOCAB / name, encoding="utf-8") as fh:
        return {r["token"]: r[key] for r in csv.DictReader(fh)}


def load_set(name):
    with open(VOCAB / name, encoding="utf-8") as fh:
        return {r["token"] for r in csv.DictReader(fh)}


PARTS = load("plant_part.csv", "part")
PART_CAT = load("plant_part.csv", "category")
PROCESS = load("process.csv", "process")
# A few product forms name their source organ: a seedcake is what is left of
# pressed seed, so the part is not actually unstated.
IMPLIES_PART = {k: v for k, v in load("process.csv", "implies_part").items() if v}
PROC_CAT = load("process.csv", "category")
MODIFIER = load("modifier.csv", "modifier")
CULTURE = load_set("culture.csv")

# Words that introduce the part in a description: '...of the leaves of...'
DESC_PART = re.compile(
    r"\b(?:of|from)\s+the\s+(?:\w+\s+){0,2}?"
    r"(leaves|leaf|flowers|flower|fruits|fruit|seeds|seed|roots|root|barks|bark"
    r"|stems|stem|woods|wood|herbs|herb|bulbs|bulb|rhizomes|rhizome|peels|peel"
    r"|kernels|kernel|sprouts|sprout|buds|bud|twigs|twig|needles|needle"
    r"|whole\s+plant|aerial\s+parts?|epicarps?|thallus|gum|resin|balsam|sap)\b",
    re.I)


def tokenize(inci, genus, species):
    """INCI tokens with the binomial removed, so only vocabulary remains."""
    drop = {(genus or "").upper(), (species or "").upper()}
    out = []
    for t in re.split(r"[\s/,]+", inci.upper()):
        t = t.strip(".")
        if t and t not in drop:
            out.append(t)
    return out


def parts_from_tokens(tokens):
    seen, out = set(), []
    for t in tokens:
        p = PARTS.get(t)
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    # 'WHOLE PLANT' contributes whole_plant twice; that is already deduped.
    # A named organ beats a generic whole-plant token appearing alongside it.
    if len(out) > 1 and "whole_plant" in out:
        out = [p for p in out if p != "whole_plant"]
    return out


def parts_from_description(desc):
    if not desc:
        return []
    seen, out = set(), []
    for m in DESC_PART.finditer(desc):
        raw = re.sub(r"\s+", " ", m.group(1).strip().upper())
        p = PARTS.get(raw) or PARTS.get(raw.rstrip("S")) or (
            "whole_plant" if raw.startswith("WHOLE") else
            "aerial_part" if raw.startswith("AERIAL") else
            "peel" if raw.startswith("EPICARP") else None)
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def main():
    con = connect()
    rows = con.execute(f"""
        SELECT e.ref_no, i.inci_name, i.description, e.genus_raw, e.species_raw
        FROM {T('extract')} e JOIN {T('ingredient')} i USING(ref_no)
        ORDER BY e.ref_no""").fetchall()

    out, stats = [], Counter()
    for ref_no, inci, desc, genus, species in rows:
        toks = tokenize(inci, genus, species)

        parts = parts_from_tokens(toks)
        source = "inci" if parts else None
        if not parts:
            implied = [IMPLIES_PART[t] for t in toks if t in IMPLIES_PART]
            if implied:
                parts, source = list(dict.fromkeys(implied)), "process_implied"
        if not parts:
            parts = parts_from_description(desc)
            source = "description" if parts else None

        proc = [PROCESS[t] for t in toks if t in PROCESS]
        mods = []
        for t in toks:
            m = MODIFIER.get(t)
            if m and m not in mods:
                mods.append(m)
        culture = bool(set(toks) & CULTURE)

        stats["with_part"] += bool(parts)
        stats[f"part_from_{source}"] += bool(source)
        stats["multi_part"] += len(parts) > 1
        stats["with_process"] += bool(proc)
        stats["with_modifier"] += bool(mods)
        stats["cell_culture"] += culture

        out.append({
            "ref_no": ref_no,
            "plant_part": parts or None,
            "part_count": len(parts),
            "part_source": source,
            "part_category": PART_CAT.get(
                next((t for t in toks if t in PARTS), ""), None) if parts else None,
            "process": proc[0] if proc else None,
            "process_all": proc or None,
            "process_category": PROC_CAT.get(
                next((t for t in toks if t in PROCESS), ""), None) if proc else None,
            "process_modifiers": mods or None,
            "is_cell_culture": culture,
        })

    for col, typ in [("plant_part", "VARCHAR[]"), ("part_count", "INTEGER"),
                     ("part_source", "VARCHAR"), ("part_category", "VARCHAR"),
                     ("process", "VARCHAR"), ("process_all", "VARCHAR[]"),
                     ("process_category", "VARCHAR"),
                     ("process_modifiers", "VARCHAR[]"),
                     ("is_cell_culture", "BOOLEAN")]:
        con.execute(
            f"ALTER TABLE {T('extract')} ADD COLUMN IF NOT EXISTS {col} {typ}")

    con.execute("DROP TABLE IF EXISTS _parts")
    cols = list(out[0])
    con.execute(f"""CREATE TABLE _parts (
        ref_no INTEGER, plant_part VARCHAR[], part_count INTEGER,
        part_source VARCHAR, part_category VARCHAR, process VARCHAR,
        process_all VARCHAR[], process_category VARCHAR,
        process_modifiers VARCHAR[], is_cell_culture BOOLEAN)""")
    con.executemany(
        f"INSERT INTO _parts VALUES ({','.join(['?'] * len(cols))})",
        [[r[c] for c in cols] for r in out])
    con.execute(f"""
        UPDATE {T('extract')} e SET
            plant_part = p.plant_part, part_count = p.part_count,
            part_source = p.part_source, part_category = p.part_category,
            process = p.process, process_all = p.process_all,
            process_category = p.process_category,
            process_modifiers = p.process_modifiers,
            is_cell_culture = p.is_cell_culture
        FROM _parts p WHERE e.ref_no = p.ref_no""")
    con.execute("DROP TABLE _parts")

    _report(con, stats, len(rows))
    con.close()


def _report(con, stats, n):
    q = lambda s: con.execute(s).fetchall()
    print(f"extract rows            : {n}")
    print(f"  with plant_part       : {stats['with_part']} ({stats['with_part']/n*100:.1f}%)")
    print(f"    from INCI name      : {stats['part_from_inci']}")
    print(f"    implied by process  : {stats['part_from_process_implied']}")
    print(f"    from description    : {stats['part_from_description']}")
    print(f"  multi-part rows       : {stats['multi_part']}")
    print(f"  with process          : {stats['with_process']} ({stats['with_process']/n*100:.1f}%)")
    print(f"  with modifier         : {stats['with_modifier']}")
    print(f"  cell-culture derived  : {stats['cell_culture']}")

    parts = q(f"""SELECT p, count(*) c FROM (
                     SELECT unnest(plant_part) AS p FROM {T('extract')}
                     WHERE plant_part IS NOT NULL
                 ) GROUP BY p ORDER BY c DESC""")
    procs = q(f"""SELECT process, count(*) c FROM {T('extract')}
                 WHERE process IS NOT NULL GROUP BY 1 ORDER BY c DESC""")
    mods = q(f"""SELECT m, count(*) c FROM (
                    SELECT unnest(process_modifiers) AS m FROM {T('extract')}
                    WHERE process_modifiers IS NOT NULL
                ) GROUP BY m ORDER BY c DESC""")
    nopart = q(f"SELECT count(*) FROM {T('extract')} WHERE plant_part IS NULL")[0][0]
    combo = q(f"""SELECT family_final, list_sort(plant_part) p, count(*) c FROM {T('extract')}
                 WHERE plant_part IS NOT NULL AND family_final IS NOT NULL
                 GROUP BY 1,2 HAVING c >= 8 ORDER BY c DESC LIMIT 12""")
    multisp = q(f"""SELECT species_accepted, count(DISTINCT list_sort(plant_part)) v, count(*) c
                   FROM {T('extract')} WHERE plant_part IS NOT NULL AND species_accepted IS NOT NULL
                   GROUP BY 1 HAVING v >= 4 ORDER BY v DESC, c DESC LIMIT 12""")

    L = ["# Phase 3 — 使用部位與製程抽取報告", "",
         "全部以詞表比對完成，未使用 LLM。詞表位於 `_data/vocab/`。", "",
         f"- 有使用部位：**{stats['with_part']} / {n}**（{stats['with_part']/n*100:.1f}%）",
         f"  - 由 INCI 名稱取得：{stats['part_from_inci']}",
         f"  - 由製程反推（如 seedcake→seed）：{stats['part_from_process_implied']}",
         f"  - 由敘述補回：{stats['part_from_description']}",
         f"- 有製程：**{stats['with_process']}**（{stats['with_process']/n*100:.1f}%）",
         f"- 有製程修飾語：**{stats['with_modifier']}**",
         f"- 細胞培養來源：**{stats['cell_culture']}**",
         f"- 部位未標示（留空，不臆測）：**{nopart}**", "",
         "## 一、使用部位分布", "", "| 部位 | 列數 |", "| --- | --- |"]
    L += [f"| {r[0]} | {r[1]} |" for r in parts]

    L += ["", "## 二、製程分布", "", "| 製程 | 列數 |", "| --- | --- |"]
    L += [f"| {r[0]} | {r[1]} |" for r in procs]

    L += ["", "## 三、製程修飾語", "", "| 修飾語 | 列數 |", "| --- | --- |"]
    L += [f"| {r[0]} | {r[1]} |" for r in mods]

    L += ["", "## 四、科 × 部位的集中處", "",
          "同一科的萃取物集中使用哪個部位，是 Phase 5 關聯分析的輸入之一。", "",
          "| 科 | 部位 | 列數 |", "| --- | --- | --- |"]
    L += [f"| {r[0]} | {', '.join(r[1])} | {r[2]} |" for r in combo]

    L += ["", "## 五、可橫向比較的物種", "",
          "同一物種被以四種以上不同部位收錄者。同物種不同部位的成分譜可能天差地遠，"
          "這些是最適合做橫向比較的群組。", "",
          "| 物種 | 部位種類數 | 萃取物數 |", "| --- | --- | --- |"]
    L += [f"| {r[0]} | {r[1]} | {r[2]} |" for r in multisp]

    checks = [
        ("部位涵蓋率 > 75%", stats["with_part"] / n > 0.75),
        ("製程涵蓋率 > 90%", stats["with_process"] / n > 0.90),
        ("複合部位已拆成多值",
         q(f"SELECT count(*) FROM {T('extract')} WHERE part_count > 1")[0][0] > 0),
        ("未標示部位者留空，未臆測為全株",
         q(f"SELECT count(*) FROM {T('extract')} WHERE plant_part IS NULL "
           "AND part_source IS NOT NULL")[0][0] == 0),
    ]
    L += ["", "## 六、驗收檢查", "", "| 檢查項 | 結果 |", "| --- | --- |"]
    L += [f"| {lab} | {'✅ 通過' if ok else '❌ 失敗'} |" for lab, ok in checks]
    print("\n驗收：")
    for lab, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {lab}")

    REPORTS.mkdir(exist_ok=True)
    (REPORTS / f"parts-process-report{SUFFIX}.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {REPORTS / ('parts-process-report' + SUFFIX + '.md')}")


if __name__ == "__main__":
    main()
