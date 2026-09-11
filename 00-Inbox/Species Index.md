---
tags:
  - index
---

# Species Index

依科分群的全部物種索引。

## 物種總覽

```dataview
TABLE
  family AS "科",
  order AS "目",
  extracts AS "萃取物數",
  compounds AS "化合物數"
FROM "10-Species"
SORT family ASC, extracts DESC
```

## 萃取物最多的物種（Top 30）

```dataview
TABLE
  family AS "科",
  extracts AS "萃取物數",
  compounds AS "化合物數"
FROM "10-Species"
SORT extracts DESC
LIMIT 30
```

## 無化合物資料的物種

```dataview
TABLE
  family AS "科",
  extracts AS "萃取物數"
FROM "10-Species"
WHERE compounds = 0
SORT extracts DESC
LIMIT 50
```
