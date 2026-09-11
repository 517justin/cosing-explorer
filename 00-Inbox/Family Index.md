---
tags:
  - index
---

# Family Index

依原料數排序的全部科索引。

## 全部科

```dataview
TABLE
  order AS "目",
  kingdom AS "界",
  species_count AS "物種數",
  extract_count AS "萃取物數",
  compounds AS "化合物數"
FROM "20-Family"
SORT extract_count DESC
```

## 化合物最豐富的科（Top 20）

```dataview
TABLE
  species_count AS "物種數",
  extract_count AS "萃取物數",
  compounds AS "化合物數"
FROM "20-Family"
WHERE compounds > 0
SORT compounds DESC
LIMIT 20
```

## 無化合物資料的科

```dataview
TABLE
  species_count AS "物種數",
  extract_count AS "萃取物數"
FROM "20-Family"
WHERE compounds = 0
SORT extract_count DESC
```
