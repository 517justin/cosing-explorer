# `_data/corrections/` — 修正的單一事實來源

`_data/COSING_CAS.csv` 是唯讀原始資料，**永不修改**。所有偏離原始資料的值，都必須能追溯到這個目錄中的某一列。無來源的修正視為 bug。

## 判定準則

修正只在滿足以下**至少一項**時才寫入：

1. **同庫內證據** — 同一個名稱的正確拼法在本資料集中已存在且出現次數更多
   （例：`Laminaceae` 1 筆 vs `Lamiaceae` 139 筆）
2. **交叉欄位矛盾** — `INCI name` 與 `Chem/IUPAC Name / Description` 對同一分類單元給出不同拼法，且其中一種為已知正確形式
   （例：INCI `CRINUM ASIATICUM` vs 敘述 `Crinium asiaticum`）
3. **命名法權威** — 該名稱在現行命名規約下非合法名，或已被 APG IV 處理
   （例：`Palmaceae` 從未被合法發表；`Compositae` 為 `Asteraceae` 的保留異名）

**不滿足以上任一項者，不改。** 兩個名稱都是真實存在的分類單元時（如 `Viola` / `Virola`、`Polygonum` / `Polygonatum`），即使拼字相近也一律保留原值。

## 檔案

| 檔案 | 內容 | correction_type | 套用者 |
| --- | --- | --- | --- |
| `family_typo.csv` | 科名拼字錯誤（15 列） | `typo` | `02_clean.py` |
| `family_apg.csv` | 舊科名 → APG IV 接受名（32 列） | `nomenclature` | `02_clean.py` |
| `taxon_typo.csv` | 屬名 / 種小名拼字錯誤（9 列） | `typo` | `02_clean.py` |
| `split_families.csv` | **不可**在科層級映射者（3 列） | — | `04_gbif.py` |
| `conflicts.csv` | INCI 與敘述學名矛盾 | `manual` | `03_parse_taxon.py` 產生 |

## `correction_type` 的意義

下游分析必須能區分這兩者，因為可信度不同：

- **`typo`** — 修的是打字錯誤。原始資料本來就想寫成修正後的樣子。可信度高，無爭議。
- **`nomenclature`** — 換的是分類系統。原始資料在它的年代是正確的，是分類學共識改變了。這類修正**會隨 APG 版本更新而改變**，`source` 欄記錄依據的版本。
- **`format`** — 空白、大小寫、分隔符等格式正規化，不涉及語意。
- **`manual`** — 人工裁決，必須在 `resolution_note` 說明依據。

## 套用順序

```
family_typo → family_apg
```

先修拼字再換命名系統。`Palmaceae` 走 `family_typo` 直接到 `Arecaceae`；`Palmae` 走 `family_apg` 到 `Arecaceae`。兩條路徑收斂到同一個節點。

## 新增修正時

1. 先確認滿足上面三條判定準則之一
2. 加一列到對應檔案，`evidence` / `note` 欄必填
3. 重跑 `02_clean.py`，檢查 `90-Reports/cleaning-report.md` 的差異
4. `git diff` 確認只有預期的列改變
