# COSING 資料剖析報告

由 `_scripts/00_profile.py` 自 `_data/kb.duckdb` 產生。原始檔 `_data/COSING_CAS.csv`（唯讀）。

## 一、規模

| 項目 | 值 |
| --- | --- |
| 成分總列數 | 13,622 |
| 生物來源萃取物 | 3,862（28.4%）|
| 純化學品 | 9,760（71.6%）|

## 二、欄位剖析

| 欄位 | 空值率 | 唯一值 | 最大長度 |
| --- | --- | --- | --- |
| `ref_no` | 0.0% | 13,622 | 5 |
| `inci_name` | 0.0% | 13,621 | 97 |
| `inn_name` | 96.3% | 476 | 50 |
| `ph_eur_name` | 98.7% | 179 | 45 |
| `cas_raw` | 0.0% | 10,013 | 128 |
| `description` | 0.8% | 13,307 | 1179 |
| `restriction` | 92.1% | 552 | 400 |
| `function_raw` | 0.5% | 1,468 | 136 |
| `update_date` | 0.0% | 465 | 10 |

`update_date` 範圍：2010-10-15 ~ 2019-11-21

## 三、CAS 欄位品質

| 項目 | 列數 |
| --- | --- |
| 多值 CAS（>1 個編號） | 967 |
| 標記 (generic) | 93 |
| 無可解析 CAS | 2 |
| 含無法解析的殘留文字 | 23 |

> 原始檔中**每一列**的 CAS 欄都帶前導 U+00A0（不斷行空白），且分隔符混用 `;`、` / `、`,`。載入時一律正規化。

## 四、生物來源列的解析狀態

| taxon_status | 列數 | 說明 |
| --- | --- | --- |
| `agree` | 3776 | INCI 與敘述兩路徑一致，自動採用 |
| `inci_not_binomial` | 32 | INCI 為俗名/商品名，學名取自敘述 |
| `species_mismatch` | 23 | 兩路徑物種不同，待人工裁決 |
| `genus_level_entry` | 17 | INCI 只到屬層級（如 CITRUS SPECIES） |
| `hyphen_split` | 6 | INCI 把連字號學名拆成兩個詞 |
| `inci_truncated` | 4 | INCI 截斷了種下名，敘述較完整 |
| `genus_mismatch` | 2 | 兩路徑屬不同，待人工裁決 |
| `desc_unparsed` | 1 | 敘述無可解析學名 |
| `spelling_variant` | 1 | 編輯距離 1 的拼字差異，採用 INCI 寫法 |

## 五、科名分布（正規化後）

| 科 | 萃取物數 | 原始寫法數 |
| --- | --- | --- |
| Lamiaceae | 293 | 3 |
| Rosaceae | 274 | 1 |
| Asteraceae | 260 | 2 |
| Fabaceae | 248 | 2 |
| Rutaceae | 192 | 1 |
| Poaceae | 154 | 2 |
| Apiaceae | 141 | 3 |
| Pinaceae | 118 | 1 |
| Malvaceae | 99 | 4 |
| Myrtaceae | 84 | 1 |
| Cupressaceae | 71 | 3 |
| Lauraceae | 66 | 1 |
| Solanaceae | 55 | 1 |
| Oleaceae | 54 | 1 |
| Zingiberaceae | 53 | 1 |
| Brassicaceae | 53 | 2 |
| Arecaceae | 50 | 3 |
| Ericaceae | 47 | 2 |
| Cucurbitaceae | 42 | 1 |
| Rubiaceae | 40 | 1 |

## 六、非植物生物來源

資料集名為「植物萃取物」，但實際含藻類、真菌、地衣、酵母與苔蘚。統計時必須分流，否則「植物」結論會被污染。

| 類群 | 列數 |
| --- | --- |
| algae | 47 |
| fungi | 11 |
| lichen | 7 |
| yeast | 3 |
| moss | 1 |

## 七、用途（Function）受控詞彙

共 **70** 個詞彙。前 20 名：

| 用途 | 全庫 | 生物來源 |
| --- | --- | --- |
| SKIN CONDITIONING | 4741 | 2276 |
| PERFUMING | 2654 | 709 |
| SURFACTANT | 1578 | 8 |
| EMULSIFYING | 1402 | 7 |
| EMOLLIENT | 1340 | 282 |
| HAIR CONDITIONING | 1196 | 194 |
| MASKING | 988 | 625 |
| VISCOSITY CONTROLLING | 776 | 57 |
| CLEANSING | 748 | 33 |
| ANTISTATIC | 680 | 3 |
| ANTIOXIDANT | 579 | 216 |
| SKIN PROTECTING | 515 | 248 |
| FILM FORMING | 496 | 35 |
| HUMECTANT | 482 | 146 |
| SOLVENT | 407 | 1 |
| ANTIMICROBIAL | 324 | 76 |
| ASTRINGENT | 293 | 218 |
| TONIC | 285 | 260 |
| BINDING | 276 | 30 |
| EMULSION STABILISING | 253 | 14 |

## 八、法規限制（Restriction）

- 帶限制的成分：**1,073**（其中生物來源 **159**）

| Annex | 列數 |
| --- | --- |
| III | 575 |
| IV | 192 |
| V | 120 |
| II | 119 |
| 其他 | 41 |
| VI | 26 |
