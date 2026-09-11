---
tags:
  - index
---

# Part Index

全部使用部位，依涉及物種數排序。

```dataview
TABLE
  species_count AS "物種數"
FROM "30-MOC"
WHERE type = "part"
SORT species_count DESC
```
