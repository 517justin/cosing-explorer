---
tags:
  - index
---

# Process Index

全部製程，依涉及物種數排序。

```dataview
TABLE
  species_count AS "物種數"
FROM "30-MOC"
WHERE type = "process"
SORT species_count DESC
```
