# 法規層 — 現行 Annex 與 2019 快照的對照

由 `_scripts/09_link_regulation.py` 產生。法規資料為 `_data/cosing_2026/`（2389 條 Annex 條文），與唯讀的 2019 快照分開存放。

## 一、兩條連結路徑

| 來源 | 連結數 | 說明 |
| --- | --- | --- |
| `snapshot_2019` | 1125 | 從 2019 `restriction` 欄解析出的引用，其中 1094（97.2%）在現行條文中仍找得到 |
| `annex_2026` | 2007 | 現行 Annex 條文自己列出的適用成分編號 |

生物來源萃取物受限數：2019 快照 **158** → 現行 **154**。

> 兩者不是同一件事。前者是「2019 年 COSING 這樣標」，後者是「現行法規今天這樣管」。合併使用會把兩個時點混為一談。

## 二、現行法規下，生物來源萃取物涉及最多的條文

| 條文 | 內容 | 萃取物數 | 科數 |
| --- | --- | --- | --- |
| II/358 | Furocoumarines (e.g. trioxysalen (INN), 8-methoxypsoralen, 5-methoxypsoralen) except for n | 60 | 2 |
| III/123 | Cupressus sempervirens oil and extract | 10 | 1 |
| III/110 | Pinus sylvestris oil and extract | 9 | 1 |
| III/103 | Abies alba oil and extract | 6 | 1 |
| II/360 | Safrole, except for normal content in the natural essences used and provided that the conc | 6 | 1 |
| III/122 | Cedrus atlantica oil and extract | 6 | 1 |
| III/115 | Pinus species oil and extract | 5 | 1 |
| III/156 | Cuminum cyminum oil and extract | 5 | 1 |
| III/107 | Abies balsamea oil and extract | 4 | 1 |
| III/320 | Indigofera tinctoria, dried and pulverised leaves of Indigofera tinctoria L | 4 | 1 |
| III/112 | Pinus palustris oil and extract | 4 | 1 |
| III/109 | Pinus mugo leaf and twig oil and extract | 3 | 1 |

## 三、2019 之後才被納管的萃取物（依科）

這些成分在我們的 2019 快照中沒有任何限制標記，但現行 Annex 條文已將其列入。

| 科 | 新增受限數 |
| --- | --- |
| Fabaceae | 4 |
| Pinaceae | 1 |

反向：2019 有標記但不在現行條文適用清單中者 **9** 筆（可能為條文改號、除名，或現行條文未逐一列出成分）。


## 四、各科在現行法規下的受限情形

| 科 | 受限萃取物數 |
| --- | --- |
| Rutaceae | 58 |
| Pinaceae | 55 |
| Cupressaceae | 10 |
| Apiaceae | 7 |
| Fabaceae | 7 |
| Lauraceae | 7 |
| Parmeliaceae | 4 |
| Altingiaceae | 4 |

## 五、查詢方式

已建立 view `extract_regulation`，一次接起萃取物、分類階層、部位製程與法規條文：

```sql
SELECT inci_name, family_final, plant_part,
       annex_no || '/' || annex_ref AS 條文,
       regulated_substance, max_concentration, product_type
FROM extract_regulation
WHERE source = 'annex_2026' AND family_final = 'Rutaceae'
```

## 六、未解析的 restriction 文字

14 筆 `restriction` 不含任何 Annex 引用（如 `Suspected carcinogen based on ECHA`、`Reported Functions as Fragrance Ingredients`）。這些**沒有被丟棄**，存於 `restriction_unparsed` 表。

另有 19 筆文字中提到 CMR 分類（致癌／致突變／生殖毒性），存於 `ingredient_cmr` 表。

## 七、驗收檢查

| 檢查項 | 結果 |
| --- | --- |
| regulation 表已載入 | ✅ 通過 |
| 2019 引用解析率 > 80% | ✅ 通過 |
| 兩條連結路徑都有資料 | ✅ 通過 |
| 未解析文字有保留，未丟棄 | ✅ 通過 |
| view extract_regulation 可查詢 | ✅ 通過 |
