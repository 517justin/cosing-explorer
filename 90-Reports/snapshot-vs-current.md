# 2019 快照 vs 2026 現況

由 `_scripts/11_load_inventory.py` 產生。兩份資料以獨立資料表並存，**不合併、不覆蓋**——Phase 0–3 的所有報告與驗收都錨定在 2019 快照上。

## 一、規模對照

| | 筆數 |
| --- | --- |
| `ingredient`（2019-11-21 快照） | 13,622 |
| `inventory_2026`（_data/cosing_2026） | 33,638 |
| 兩邊都有（依 COSING Ref No） | 13,441 |
| 只在 2019（已下架或改編號） | 181 |
| 只在 2026 | 20,197 |

## 二、⚠️ 2019 快照本身就不完整

2019 CSV 的編號範圍是 **31364–97704**。該範圍內，現行資料庫有 **27,170** 筆，而我們的 CSV 只收錄 **13,622** 筆——
**涵蓋率 50.1%**。

換句話說，`COSING_CAS.csv` 從來就不是 2019 年的完整匯出，而是**約一半的子集**。兩邊都有的 13,441 筆全部是 `Active` 狀態，但範圍內未被收錄的那些也有 99.7% 是 `Active`，所以差異不能用「只匯出有效項目」來解釋。

> **這會影響如何解讀 Phase 0–3 的所有統計。**「3,862 筆生物來源」「前 10 大科佔 48%」「40% 物種只出現一次」這些都是那個子集的樣貌，不是 COSING 2019 年的全貌。結論的方向多半仍成立，但比例不可當作母體比例引用。

## 三、生物來源萃取物的成長

| | 筆數 |
| --- | --- |
| 2019 快照中的生物來源（`extract`） | 3,862 |
| 2026 新增中敘述含科名者 | 3,871 |
| 合計可用的生物來源（概估） | ~7,733 |

**生物來源萃取物大約翻倍。** 若要重建圖譜，Phase 1–3 的管線可直接套用在新資料上（欄位對應相同），但科名／學名的錯字對照表需重新掃描——新資料會帶來新的錯字。

## 四、狀態分布（2026）

| status | 筆數 |
| --- | --- |
| Active | 30,386 |
| (空 = Not active) | 3,252 |

## 五、INCI 名稱被修訂者

共 **12** 筆。其中數筆正好是 Phase 1 人工修正過的連字號問題——COSING 後來自己改了，等於反向驗證了當初的判斷。

| Ref No | 2019 | 2026 |
| --- | --- | --- |
| 41490 | PROPYLIDENE PHTHALIDE | 3-PROPYLIDENEPHTHALIDE |
| 41601 | 2,2'-METHYLENEBIS-4-AMINOPHENOL | 2,2'-METHYLENEBIS 4-AMINOPHENOL |
| 54293 | ALISMA PLANTAGO AQUATICA EXTRACT | ALISMA PLANTAGO-AQUATICA EXTRACT |
| 55581 | DAUCUS CAROTA SATIVA LEAF EXTRACT | DAUCUS CAROTA LEAF EXTRACT |
| 59006 | PERFLUOROOCTYL TRIETHOXYSILANE | PERFLUOROHEXYLETHYL TRIETHOXYSILANE |
| 59729 | SODIUM TRIMETHYLPENTENE/MA COPOLYMER | SODIUM MA/DIISOBUTYLENE COPOLYMER  |
| 84098 | FERULA ASSA FOETIDA GUM EXTRACT | FERULA ASSA-FOETIDA GUM EXTRACT |
| 90698 | CITRUS RETICULATA EXTRACT | CITRUS NOBILIS PEEL EXTRACT |
| 91623 | CURCUBITURILS | CUCURBITURILS |
| 94090 | BUTYL METHACRYLATE/ACRYOYLOXY PG METHACRYLATE COPOLYMER | BUTYL METHACRYLATE/ACRYLOYLOXY PG METHACRYLATE COPOLYMER |
| 95608 | BIS-PIPERAZINE | BIS-(DIETHYLAMINOHYDROXYBENZOYL BENZOYL) PIPERAZINE |
| 95758 | BIS-PCA DIMETHICONE | BIS-4-PCA DIMETHICONE |

## 六、查詢方式

```sql
-- 某個科在新資料中多了哪些萃取物
SELECT n.ref_no, n."inciName"
FROM inventory_2026 n
WHERE n.ref_no NOT IN (SELECT ref_no FROM ingredient)
  AND n."chemicalDescription" LIKE '%Lamiaceae%';
```

## 七、驗收檢查

| 檢查項 | 結果 |
| --- | --- |
| inventory_2026 已載入 | ✅ 通過 |
| ref_no 可對應 2019 快照 | ✅ 通過 |
| 2019 快照未被更動 | ✅ 通過 |
| 兩表並存，未合併 | ✅ 通過 |
