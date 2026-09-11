---
tags:
  - dashboard
---

# CosIng 化妝品成分探索器 Dashboard

> 線上版：[517justin.github.io/cosing-explorer](https://517justin.github.io/cosing-explorer/)

## 總覽

| 類別 | 筆記數 |
|------|--------|
| 🌿 物種 | `$= dv.pages('"10-Species"').length` |
| 🏷️ 科 | `$= dv.pages('"20-Family"').length` |
| 📋 MOC | `$= dv.pages('"30-MOC"').length` |

---

## 索引

- [[Species Index]] — 全部物種，依科分群
- [[Family Index]] — 全部科，依原料數排序
- [[Function Index]] — 82 種用途
- [[Part Index]] — 28 種使用部位
- [[Process Index]] — 26 種製程
- [[Kingdom Index]] — 依界（Plantae / Fungi / Chromista）分群
- [[Compound Hotspots]] — 化合物最豐富的物種

---

## 最近修改

```dataview
TABLE file.mtime AS "修改時間"
FROM "10-Species" OR "20-Family" OR "30-MOC"
SORT file.mtime DESC
LIMIT 15
```
