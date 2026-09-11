---
tags:
  - index
---

# Function Index

全部用途（Function），依涉及物種數排序。

```dataview
TABLE
  species_count AS "物種數",
  family_count AS "科數"
FROM "30-MOC"
WHERE type = "function"
SORT species_count DESC
```
