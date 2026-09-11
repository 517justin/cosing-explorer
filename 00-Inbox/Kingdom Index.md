---
tags:
  - index
---

# Kingdom Index

依界（Kingdom）分群的物種索引。

## Plantae（植物界）

```dataview
TABLE
  family AS "科",
  extracts AS "萃取物數",
  compounds AS "化合物數"
FROM "10-Species"
WHERE kingdom = "Plantae"
SORT family ASC, extracts DESC
```

## Fungi（真菌界）

```dataview
TABLE
  family AS "科",
  extracts AS "萃取物數",
  compounds AS "化合物數"
FROM "10-Species"
WHERE kingdom = "Fungi"
SORT extracts DESC
```

## Chromista（藻類 / 卵菌）

```dataview
TABLE
  family AS "科",
  extracts AS "萃取物數",
  compounds AS "化合物數"
FROM "10-Species"
WHERE kingdom = "Chromista"
SORT extracts DESC
```

## 未分類

```dataview
TABLE
  family AS "科",
  extracts AS "萃取物數"
FROM "10-Species"
WHERE !kingdom
SORT extracts DESC
```
