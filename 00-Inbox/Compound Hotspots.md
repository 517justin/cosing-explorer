---
tags:
  - index
---

# Compound Hotspots

化合物數量最多的物種與科，代表化學研究最深入的生物來源。

## 化合物最豐富的物種（Top 50）

```dataview
TABLE
  family AS "科",
  kingdom AS "界",
  extracts AS "萃取物數",
  compounds AS "化合物數"
FROM "10-Species"
WHERE compounds > 0
SORT compounds DESC
LIMIT 50
```

## 化合物最豐富的科（Top 30）

```dataview
TABLE
  species_count AS "物種數",
  extract_count AS "萃取物數",
  compounds AS "化合物數",
  round(compounds / species_count, 1) AS "化合物/物種"
FROM "20-Family"
WHERE compounds > 0
SORT compounds DESC
LIMIT 30
```

## 萃取物多但化合物資料少的物種

> LOTUS 查不到 ≠ 該生物沒有成分，僅代表文獻未收錄。此清單為潛在研究空白。

```dataview
TABLE
  family AS "科",
  extracts AS "萃取物數",
  compounds AS "化合物數"
FROM "10-Species"
WHERE extracts >= 5 AND compounds = 0
SORT extracts DESC
LIMIT 30
```
