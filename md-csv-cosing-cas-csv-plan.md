---
tags: [專案/知識圖譜]
status: 修訂版
created: 2026-08-11
revised: 2026-08-13
---

# 植物萃取物知識圖譜 — 實作計劃（修訂版）

## Context — 為什麼要改寫原計劃

原計劃 `植物萃取物知識圖譜-實作計劃.md` 是在**還沒看過實際 CSV** 的情況下寫的，對資料做了四個假設，其中三個與 `COSING_CAS.csv` 的實況不符。照原計劃執行會在 Phase 1 就整個走偏——原計劃把 Phase 1（學名正規化）標為「成敗關鍵、2–3 天、必須用 LLM 抽取中文俗名」，但實際資料裡學名是**結構化的拉丁二名法**，根本不需要 LLM，也不存在中文俗名歧義問題。

同時，使用者指出 CSV 內有錯字需先修正。經全庫掃描確認：錯字確實存在且**集中在科名與屬名**，若不先修正，知識圖譜的核心結構（科屬階層）會裂成重複節點，Phase 5 的所有關聯分析都會失真。

本修訂版的目的：**把計劃重新錨定在真實資料上**，並把「錯字修正」從一個模糊的前置動作，變成一個有具體清單、可驗證、可回溯的 Phase。

---

## 一、原計劃 vs 實際資料

| 項目 | 原計劃假設 | 實際 `COSING_CAS.csv` | 影響 |
| --- | --- | --- | --- |
| 資料筆數 | 約 10,000 筆植物萃取物 | 13,622 筆**全部化妝品成分**，其中生物來源萃取物僅 3,862 筆 | 🔴 範圍需重定義 |
| 語言 | 中文敘述、中文俗名 | 英文敘述 + 拉丁學名（INCI 標準命名） | 🔴 Phase 1 整段作廢重寫 |
| 學名取得 | LLM 抽取 → GBIF 驗證 | **INCI 名稱前兩詞即屬種名**，敘述末尾直接寫科名 | 🟢 改為規則解析，成本大降 |
| 科（family） | 需靠 GBIF 補 | **敘述中已直接標示**（3,862 筆有科名） | 🟢 Phase 2 從補資料變成校驗 |
| 使用部位 | 從敘述抽取 | INCI 名稱中即為固定 token（LEAF/ROOT/SEED…） | 🟢 純字典比對 |
| 用途分類 | CSV 既有欄位 | `Function` 欄，70 個受控詞彙 | 🟢 符合預期 |
| 生物類群 | 純植物 | 另含藻類 47、真菌 11、地衣 7、酵母 3、苔蘚 1 | 🟡 專案名稱與本體需調整 |
| 化學結構 | 完全沒有 | 確實沒有 SMILES/InChI，但有 CAS No（10,008 個唯一值） | 🟢 CAS 可作為 LOTUS/PubChem 的第二條 join 路徑 |

**結論：原計劃最貴的 Phase 1（2–3 天）縮短為約 0.5 天，省下的預算轉投到「資料清理」與「Phase 5 關聯分析」。**

---

## 二、資料實況剖析（已完成，取代原 Phase 0 的大部分工作）

### 檔案層級

- 編碼 UTF-8 **含 BOM**（讀取須用 `utf-8-sig`），換行 CRLF
- 13,622 資料列，每列固定 9 欄，**無欄位錯位、無破損引號**（結構乾淨）
- 欄位名 `Ph.\xa0Eur. Name` 含 **non-breaking space (U+00A0)**，直接用字串比對會取不到

### 欄位剖析

| 欄位 | 空值率 | 唯一值 | 備註 |
| --- | --- | --- | --- |
| `COSING Ref No` | 0% | 13,622 | 天然主鍵，完全唯一 |
| `INCI name` | 0% | 13,621 | 1 組重複：`PPG-70 BIS-(2-AMINOPROPYL) ETHER` |
| `INN name` | 96.3% | 477 | 幾乎空，低價值 |
| `Ph. Eur. Name` | 98.7% | 180 | 幾乎空，低價值 |
| `CAS No` | 0% | 10,008 | **每一列都有前導空白**；43 列多值 |
| `Chem/IUPAC Name / Description` | 0.8% | 13,308 | 核心欄位，最長 1,179 字元 |
| `Restriction` | 92.1% | 552 | Annex 引用：III=575, IV=192, V=120, II=119, VI=26 |
| `Function` | 0.5% | 1,468 組合 | 拆開後為 **70 個受控詞彙** |
| `Update Date` | 0% | 465 | `DD/MM/YYYY`，範圍 2010-10-15 ~ 2019-11-21 |

### 敘述欄位的句型（原計劃 Phase 0 的核心產出）

生物來源列的敘述高度公式化：

```
<INCI Name> is the <製程> obtained from the <部位> of the <俗名>, <Genus species>, <Family>.
```

實測解析率：
- **95.4%** 的生物來源列，敘述以 `, <Family>.` 結尾
- **91.3%** 可用單一 regex 取出「科名前的二名法學名」
- 解析失敗的 8.7% 集中在三種型態：`var.` / `spp.` 變種標記、`(syn: …)` 同物異名括號、開頭有 `"商品俗名". ` 前綴

製程詞分布：extract 747、powder 217、volatile 195、oil 87、fixed oil 65、juice 60、wax 28、hydrolysate 19、fat 12。

### 生物來源列的判定

| 判定條件 | 筆數 |
| --- | --- |
| 敘述含 `-aceae` 結尾科名 | 3,319 |
| 敘述含**舊式科名**（Leguminosae/Labiatae/Compositae/Umbelliferae/Gramineae/Guttiferae/Palmae/Cruciferae） | 543 |
| **合計有科名者** | **3,862** |
| 有部位詞但無科名（漏網） | 158 |
| 其中非植物（藻/菌/地衣/苔/酵母） | 69 |

INCI 名稱中的部位 token（可直接字典比對）：LEAF 813、FLOWER 537、FRUIT 415、SEED 414、ROOT 339、STEM 230、BARK 129、JUICE 115、HERB 100、WOOD 88、PEEL 73、TWIG 48、GUM 42、BUD 42、RESIN 39、CALLUS 39、RHIZOME 32、KERNEL 30…（759 筆無部位 token，屬全株/未指定）

---

## 三、🔴 錯字與資料品質問題清單

這是本次修訂新增的核心章節。所有項目皆為**實際掃描全庫後確認**，非推測。

### 3.1 科名拼字錯誤（真錯字）

同一個科同時存在正確與錯誤拼法，或明顯拼錯：

| 錯誤寫法 | 出現數 | 正確寫法 | 判定依據 |
| --- | --- | --- | --- |
| `Laminaceae` | 1 | `Lamiaceae` | 同庫內 Lamiaceae 有 139 筆 |
| `Cypressaceae` | 3 | `Cupressaceae` | 同庫內 Cupressaceae 有 63 筆 |
| `Anacardaceae` | 3 | `Anacardiaceae` | 同庫內 Anacardiaceae 有 29 筆 |
| `Apieaceae` | 1 | `Apiaceae` | 同庫內 Apiaceae 有 67 筆 |
| `Borraginaceae` | 1 | `Boraginaceae` | 同庫內 Boraginaceae 有 20 筆 |
| `Elagnaceae` | 3 | `Elaeagnaceae` | 同庫內 Elaeagnaceae 有 8 筆 |
| `Valeriabaceae` | 1 | `Valerianaceae` | 同庫內 Valerianaceae 有 13 筆 |
| `Zygopuhyllaceae` | 1 | `Zygophyllaceae` | 同庫內 Zygophyllaceae 有 15 筆 |
| `Cannabidaceae` | 2 | `Cannabaceae` | 同庫內 Cannabaceae 有 8 筆 |
| `Anonaceae` | 7 | `Annonaceae` | 同庫內 Annonaceae 有 3 筆 |
| `Callophyllaceae` | 1 | `Calophyllaceae` | 拼字錯誤 |
| `Maranthaceae` | 1 | `Marantaceae` | 拼字錯誤 |
| `Furaceae` | 3 | `Fucaceae` | 藻類科，同庫內 Fucaceae 有 9 筆 |
| `Simarubaceae` | 8 | `Simaroubaceae` | 同庫內 Simaroubaceae 有 1 筆 |
| `Palmaceae` | 35 | `Arecaceae` | **非合法科名**，同庫內 Arecaceae 有 12 筆、Palmae 有 3 筆 |

> ⚠️ `Palmaceae`(35) / `Palmae`(3) / `Arecaceae`(12) 三種寫法並存，同一個科在圖上會裂成**三個節點**。這類問題正是必須先清理的原因。

### 3.2 屬名 / 種小名拼字錯誤

以「編輯距離近似分群 + INCI 名稱 vs 敘述二名法交叉比對」兩種方法獨立驗出：

| 錯誤寫法 | 出現數 | 正確寫法 |
| --- | --- | --- |
| `Butyrospernum` | 3 | `Butyrospermum` |
| `Crinium` | 3 | `Crinum` |
| `Agastachye` | 2 | `Agastache` |
| `Vacciniium` | 1 | `Vaccinium` |
| `Jasminium` | 1 | `Jasminum` |
| `Diospypros` | 1 | `Diospyros` |
| `Bertholetia` | 1 | `Bertholletia` |
| `Anona` | 1 | `Annona` |
| `Capparis mooni` | 1 | `Capparis moonii` |

**誤判排除**（兩者皆為真實存在的屬，不可改）：Ailanthus/Galanthus、Calophyllum/Caulophyllum、Chrysanthellum/Chrysanthemum、Dipterocarpus/Pterocarpus、Polygonatum/Polygonum、Viola/Virola。

### 3.3 內容矛盾（不是錯字，是資料錯誤 — 需人工判定，不可自動改）

INCI 名稱與敘述中的學名互相矛盾，共 115 組，其中真正矛盾者需逐一裁決：

| INCI 名稱 | 敘述中學名 | 性質 |
| --- | --- | --- |
| `ROSA RUGOSA *`（4 筆） | `Rosa rubiginosa` | **不同物種**，須人工確認何者為真 |
| `ANGELICA POLYMORPHA SINENSIS ROOT EXTRACT` | `Angelica sinensis` | 三名法，INCI 截斷所致 |
| `ALGAE EXTRACT` | `Fucus vesiculosus` | 泛稱 vs 具體種 |

其餘多數為可規則化處理的型態：`HYDROLYZED <屬名>` 前綴（水解前綴吃掉屬名位置）、`<屬> SPECIES` ↔ `<屬> spp`、`CITRUS PARADISI, X C. RETICULATA` 雜交種（27 筆）、`ROSA HYBRID` ↔ `Rosa hybrida`。

### 3.4 格式問題

| 問題 | 影響範圍 | 處理 |
| --- | --- | --- |
| `CAS No` 每列皆有**前導空白** | 13,622 列（100%） | 一律 `.strip()` |
| CAS 含註記 `(generic)` / `(Generic)` 大小寫不一 | 約 90 列 | 抽出旗標另存欄位 |
| CAS 多值分隔符不一致：`;`、` / `、`,` 混用 | 783 種非標準 token / 1,017 次出現 | 統一拆成多值陣列 |
| CAS 佔位值 `999999-99-4` | 1 列 | 視為 NULL |
| 欄位名含 U+00A0（`Ph.\xa0Eur. Name`） | 表頭 | 讀入即重新命名為 snake_case |
| BOM | 檔頭 | `encoding='utf-8-sig'` |

### 3.5 「正確但過時」的舊科名（需正規化到 APG IV）

這**不是錯字**，是 COSING 沿用的舊分類系統名稱。但若不統一，同一個科會在圖上分裂。已確認採用「正規化到 APG IV，保留原始寫法欄位」。

**可直接一對一映射：**

| 原寫法 | 出現數 | APG IV 接受名 |
| --- | --- | --- |
| Leguminosae | 162 | Fabaceae |
| Labiatae | 153 | Lamiaceae |
| Compositae | 110 | Asteraceae |
| Umbelliferae | 73 | Apiaceae |
| Gramineae | 43 | Poaceae |
| Guttiferae | 6 | Clusiaceae |
| Palmae / Palmaceae | 3 / 35 | Arecaceae |
| Cruciferae | 2 | Brassicaceae |
| Tiliaceae / Sterculiaceae / Bombacaceae | 20 / 19 / 6 | Malvaceae |
| Agavaceae / Ruscaceae | 16 / 2 | Asparagaceae |
| Punicaceae | 15 | Lythraceae |
| Chenopodiaceae | 15 | Amaranthaceae |
| Valerianaceae / Dipsacaceae | 13 / 1 | Caprifoliaceae |
| Hippocastanaceae / Aceraceae | 8 / 1 | Sapindaceae |
| Asclepiadaceae | 5 | Apocynaceae |
| Taxodiaceae | 5 | Cupressaceae |
| Illiciaceae | 4 | Schisandraceae |
| Fumariaceae | 3 | Papaveraceae |
| Myrsinaceae | 3 | Primulaceae |
| Samydaceae / Flacourtiaceae | 2 / 1 | Salicaceae |
| Capparidaceae | 2 | Capparaceae |
| Cuscutaceae | 1 | Convolvulaceae |
| Hydrophyllaceae | 1 | Boraginaceae |
| Julianiaceae | 1 | Anacardiaceae |
| Pyrolaceae | 1 | Ericaceae |
| Xanthorrhoeaceae | 1 | Asphodelaceae |

> ⚠️ **不可在科層級映射者**：`Liliaceae`(53) 與 `Scrophulariaceae`(13) 在 APG IV 中被**拆分**——Liliaceae 舊義涵蓋今日的 Amaryllidaceae / Asparagaceae / Melanthiaceae / Colchicaceae；Scrophulariaceae 舊義拆入 Plantaginaceae / Orobanchaceae。這 66 筆**必須依屬名逐一判定**，交由 Phase 2 的 GBIF 查詢決定，不得寫進科名映射表。

---

## 四、修正策略（已確認）

**原檔 `COSING_CAS.csv` 永久唯讀，一個位元組都不改。**

所有修正以「對照表 + 套用腳本」實現，任何一筆修正都能回答「原值是什麼、改成什麼、憑什麼改」：

```
_data/corrections/
├── family_typo.csv        # 3.1 拼字錯誤    欄位: raw, corrected, reason, evidence
├── family_apg.csv         # 3.5 舊科名→APG IV  欄位: raw, accepted, source, retrieved_at
├── taxon_typo.csv         # 3.2 屬名/種小名錯字
├── conflicts.csv          # 3.3 內容矛盾（含 resolution 欄，未裁決者留空）
└── README.md              # 每張表的判定準則
```

修正一律標註 `correction_type` ∈ {`typo`, `nomenclature`, `format`, `manual`}，讓下游能區分「修拼字」與「換分類系統」——這兩件事的可信度不同，分析時要能分開看。

**永遠保留原始寫法欄位**：主表同時存 `family_raw` 與 `family_accepted`，物種同理。任何時候都能重現 COSING 原貌，也能對照 EU 法規文件。

---

## 五、修正後的本體設計

### 範圍（已確認：全庫入庫，萃取物建圖譜）

13,622 筆全部進 DuckDB 主表（保留 CAS / Function / Restriction 完整欄位），但**物種—屬—科的圖譜階層只建在 3,862 筆生物來源子集上**。合成化學品留在主表，透過 `Function` 與 `Restriction` 參與查詢與比較分析，但不建分類節點。

### 節點類型（依實際資料修正數量級）

| 節點 | 原計劃估計 | 實際數量級 | 來源 |
| --- | --- | --- | --- |
| 成分（全庫） | — | 13,622 | CSV 每列 |
| 生物來源萃取物 | 10,000 | **3,862** | 有科名的列 |
| 物種學名 | 數百~2,000 | **約 1,500~1,800** | INCI + 敘述解析 |
| 屬 | 數十~數百 | **711**（已實測） | 解析結果 |
| 科 | 數十~數百 | **約 200**（正規化後，原始 236 種寫法） | 敘述 + APG IV 正規化 |
| 使用部位 | < 20 | **約 30** | INCI token 字典 |
| 製程 / 萃取方法 | < 20 | **約 25** | INCI token + 敘述動詞 |
| 用途（Function） | 數十 | **70**（已實測，受控詞彙） | `Function` 欄 |
| 法規限制 | — | **Annex II–VI，552 種引用** | `Restriction` 欄（原計劃遺漏） |
| 已知成分 | 數千 | 視 LOTUS 覆蓋率 | 外部 |

### 關係類型

```
成分 --has_cas--> CAS號
成分 --categorized_as--> 用途(Function)
成分 --restricted_by--> 法規附錄(Annex)      ← 新增
萃取物 --derived_from--> 物種學名
萃取物 --uses_part--> 使用部位
萃取物 --processed_by--> 製程
物種學名 --belongs_to--> 屬 --belongs_to--> 科
物種學名 --contains--> 已知成分               ← Phase 4
```

**新增 `restricted_by`**：`Restriction` 欄是原計劃完全沒看到的一層。1,073 筆成分帶歐盟法規限制，這是化妝品領域最有行動價值的資訊之一（「這個科的萃取物有幾成受限？」），不用可惜。

### 設計原則（沿用原計劃，補充一條）

- 3,862 筆萃取物不生成 3,862 則筆記。筆記寫在物種、科、用途、部位層級。
- 圖譜價值來自「科屬階層 × 用途 × 法規限制」三者疊加。
- 外部資料標明來源與擷取日期，與人工內容分區塊存放。
- **新增：所有經過修正的欄位，必須能追溯到 `_data/corrections/` 中的某一列。** 無來源的修正視為 bug。

---

## 六、實作階段（修訂）

### Phase 0 — 資料剖析 ✅ 已完成

本文件第二章即為產出。將整理為 `90-Reports/data-profile.md`。

**驗收：** 已達成——句型已歸納（95.4% 公式化）、物種規模已知（711 屬）、結構完整性已確認（無欄位錯位）。

---

### Phase 1 — 資料清理與載入（1 天）⭐ 新的成敗關鍵

原計劃的 Phase 1（LLM 學名抽取）作廢。**真正的關鍵改為資料清理**。

- [ ] `_scripts/01_load.py`：`utf-8-sig` 讀入，欄位改 snake_case（處理 U+00A0），CAS `strip()` + 拆多值 + 抽 `(generic)` 旗標 + `999999-99-4` 轉 NULL，`Update Date` 轉 ISO 日期
- [ ] 依第三章清單建立 `_data/corrections/` 四張表
- [ ] `_scripts/02_clean.py`：套用對照表，產出 `ingredient` 主表（同時保留 `*_raw` 與 `*_accepted`）
- [ ] `_scripts/03_parse_taxon.py`：
  - 主路徑：INCI 名稱前兩詞 → 屬 + 種小名
  - 副路徑：敘述中科名前的二名法
  - **兩路徑交叉比對**，一致者自動通過（實測 3,408 筆一致 = 96.7%）
  - 不一致者（115 筆）全部寫入 `conflicts.csv` 待裁決
- [ ] 處理 8.7% 解析失敗型態：`var.` / `spp.` / `(syn:)` / `"商品名". ` 前綴

**產出：** `_data/kb.duckdb`、`_data/corrections/*.csv`、`90-Reports/cleaning-report.md`

**驗收：**
- 3,862 筆生物來源列，屬名解析率 > 98%
- 科名正規化後唯一值從 236 降到約 200，且 Palmae/Palmaceae/Arecaceae 合併為單一節點
- `conflicts.csv` 中 115 組矛盾 100% 有裁決或標記 `ambiguous`
- 每一筆修正都能在對照表中找到對應列

> ⚠️ **不要用 LLM 做學名抽取。** INCI 是標準化命名系統，規則解析可達 98%，LLM 只會引入幻覺且無法重現。LLM 在本專案的正當用途只有一個：協助**裁決** `conflicts.csv` 中的矛盾（且需附外部依據），不是抽取。

---

### Phase 2 — 分類階層驗證（0.5 天）

原計劃是「用 GBIF 補科名」，現在改為「**用 GBIF 驗證已有科名 + 解決拆分科**」。

- [ ] 對約 1,500~1,800 個物種打 GBIF species match API（免費、無金鑰、支援模糊比對）
- [ ] 取 GBIF **accepted name**（同物異名不統一會讓物種節點分裂）
- [ ] **重點：** 解決 3.5 節的 `Liliaceae`(53) 與 `Scrophulariaceae`(13) 拆分科——依屬名逐一取 GBIF family
- [ ] 交叉比對 CSV 科名 vs GBIF 科名，差異寫入 `90-Reports/family-discrepancy.md`
- [ ] 記錄 GBIF 擷取日期（APG 分類系統會更新）
- [ ] 藻類 / 真菌 / 地衣 69 筆單獨標記 `kingdom` 欄，不與植物混算

**產出：** `_data/taxonomy.csv`（欄位：raw_name, accepted_name, gbif_key, genus, family, order, kingdom, confidence, retrieved_at）

**驗收：** 已確認物種有 family 者 > 95%；Liliaceae / Scrophulariaceae 的 66 筆全部落到具體 APG IV 科；GBIF 科名與 CSV 科名不一致者 100% 有紀錄。

---

### Phase 3 — 部位與製程抽取（0.5 天）

原計劃已判斷「用規則就夠」——**正確，且比原計劃預期更簡單**，因為部位與製程直接是 INCI 名稱的 token。

- [ ] 建部位詞表（約 30 詞，實測分布見第二章）與製程詞表（約 25 詞）
- [ ] 從 INCI 名稱 token 化比對；複合部位（`FLOWER/LEAF/STEM`）拆成多值
- [ ] 759 筆無部位 token 者，回頭掃敘述；仍無者標 `whole_plant` 或 `unspecified`，**不猜**
- [ ] 製程另抽「修飾語」：`EXPRESSED`、`HYDROLYZED`、`RECTIFIED`、`EPOXIDIZED`、`SAPONIFIED`

**產出：** 主表新增 `plant_part[]`、`process`、`process_modifier` 欄

> 同一物種不同部位的成分譜可能天差地遠。不區分部位的圖譜會把不相干的東西連在一起。

---

### Phase 4 — 外部化學層富集（1 天，離線骨幹完成後才做）

已確認策略：**Phase 0–3 完全離線可完成**，外部富集作為獨立層，快取到 `_data/`，斷網時系統仍可運作。

- [ ] 下載 LOTUS TSV 至 `_data/lotus/`（化合物表含 SMILES/InChIKey、物種表、配對表）
- [ ] 以 **GBIF accepted name** join（不要用原始名）
- [ ] **第二條路徑：用 CAS No join PubChem** — 原計劃沒想到這條。10,008 個唯一 CAS 可直接換到結構，對 9,760 筆合成化學品尤其有效，能把「無結構」的缺口補掉一大塊
- [ ] 記錄覆蓋率：哪些查得到、哪些查不到，分開統計
- [ ] （可選）有 SMILES 後可用 RDKit 做 Murcko 骨架分解與 Morgan 指紋相似度

**產出：** `_data/species_compounds.csv`、`_data/cas_structures.csv`、覆蓋率報告

> ⚠️ **LOTUS 查不到 ≠ 該生物沒有成分**，只代表文獻未收錄。冷門物種覆蓋率會很低。分析時必須把「無資料」與「無成分」分開處理，否則結論全部偏向被研究得多的物種。

---

### Phase 5 — 挖掘隱藏關聯（1–2 天）

依行動價值排序，前三項**離線即可執行**：

1. **空白格推薦** ⭐ 最有價值 — 統計某 Function 的萃取物集中在哪幾個科，列出該科中 COSING 尚未收錄的物種。
2. **法規盲點分析** ⭐ 新增 — 交叉 `Restriction` 與科屬階層：某科的萃取物有幾成受 Annex 限制？同科未受限的近緣種是替代候選還是尚未被審視的風險？此分析原計劃完全沒有，但對化妝品應用最直接。
3. **用途相同但親緣極遠** — 趨同演化的真實案例，或 Function 標錯。兩種都值得查核。
4. **同科不同屬但用途一致** — 化學分類學支持，可信度最高。
5. **同物種橫向比較群組** — 同物種不同部位/製程的組合自動成組（Phase 3 產出直接支援）。
6. **成分集合相似度**（需 Phase 4）— Jaccard 相似度，只留 top-k 鄰居（k=5~10），不建全連接圖。

**產出：** `90-Reports/` 下各項分析筆記

---

### Phase 6 — Vault 生成（1 天）

沿用原計劃，數量級依實測修正。

- [ ] 物種筆記（約 1,500~1,800 則）：frontmatter 帶 accepted name、gbif_key、屬、科、kingdom
- [ ] 科筆記（約 200 則）：物種清單、Function 分布、法規限制概況、特徵化學
- [ ] 用途（70）/ 部位（30）/ 製程（25）的 MOC
- [ ] Dataview 動態索引

**機器生成區與人工撰寫區必須分開：**

```markdown
## 自動生成
<!-- AUTO-START -->
(腳本每次重跑覆寫此區)
<!-- AUTO-END -->

## 我的筆記
(腳本永不觸碰此區)
```

> 科筆記是本專案最有價值的產出。機器只能給你結構，知識要自己長。

---

### Phase 7 — AI 問答層（1–2 天）

沿用原計劃的四層混合檢索：

| 層 | 用途 | 實作 |
| --- | --- | --- |
| 精確查表 | 學名 / INCI 名 / CAS → ID | Phase 1–2 的對照表 |
| 結構化篩選 | 條件查詢（含 Function、Annex） | DuckDB SQL |
| 圖遍歷 | 「相關的還有什麼」 | 鄰接表 |
| 向量檢索 | 語意模糊的問題 | 只用於敘述欄位 |

> ⚠️ **不要用純向量 RAG。** 學名系統性命名讓近緣物種的 embedding 極為相似，純向量檢索會自信地取錯物種。名稱查詢必須走字典，不走向量。

---

## 七、目錄結構

```
vault/
├── CLAUDE.md
├── _data/
│   ├── COSING_CAS.csv          # 原始資料，唯讀，永不修改
│   ├── corrections/            # 🔴 新增：所有修正的單一事實來源
│   │   ├── family_typo.csv
│   │   ├── family_apg.csv
│   │   ├── taxon_typo.csv
│   │   ├── conflicts.csv
│   │   └── README.md
│   ├── kb.duckdb
│   ├── taxonomy.csv
│   └── lotus/
├── _scripts/
│   ├── 01_load.py              # 編碼/欄名/CAS 格式正規化
│   ├── 02_clean.py             # 套用 corrections/
│   ├── 03_parse_taxon.py       # INCI + 敘述雙路徑解析 + 交叉驗證
│   ├── 04_gbif.py
│   ├── 05_parts.py
│   └── 06_gen_notes.py
├── 00-Inbox/
├── 10-Species/                 # 約 1,500~1,800 則
├── 20-Family/                  # 約 200 則（本專案最有價值）
├── 30-MOC/                     # 用途 70 / 部位 30 / 製程 25
└── 90-Reports/
```

**版本控制：** vault 必須 `git init`。每個 Phase 開始前 commit，任何批次改寫前 commit。這不是建議事項。

---

## 八、時程（修訂）

| Phase | 內容 | 原計劃 | 修訂 | 變動原因 |
| --- | --- | --- | --- | --- |
| 0 | 資料剖析 | 0.5 | **✅ 0** | 已完成 |
| 1 | **資料清理與載入** ⭐ | 2–3 | **1** | LLM 抽取改為規則解析；但新增錯字修正工作 |
| 2 | 分類階層驗證 | 0.5 | **0.5** | 從補資料變成校驗，但多了拆分科處理 |
| 3 | 部位與製程 | 0.5 | **0.5** | INCI token 化，比預期簡單 |
| 4 | 外部化學富集 | 1 | **1** | 新增 CAS→PubChem 路徑 |
| 5 | 挖掘隱藏關聯 | 1–2 | **1.5–2** | 新增法規盲點分析 |
| 6 | Vault 生成 | 1 | **1** | — |
| 7 | AI 問答層 | 1–2 | **1–2** | — |
| | **合計** | **7.5–10.5** | **6.5–8** | |

Phase 0–2 是必做骨幹。Phase 4 之後可平行進行。

---

## 九、風險清單（修訂）

| 風險 | 影響 | 對策 | 狀態 |
| --- | --- | --- | --- |
| ~~中文俗名一名多物種~~ | — | — | ❌ 移除：資料為拉丁學名，無此風險 |
| ~~LLM 幻覺出假學名~~ | — | — | ❌ 大幅降低：改用規則解析，LLM 只參與裁決 |
| **科名三種寫法並存**（Palmae/Palmaceae/Arecaceae） | 節點分裂，同科關聯分析失真 | 3.1 + 3.5 對照表強制正規化 | 🔴 新增，已有清單 |
| **舊科名被 APG IV 拆分**（Liliaceae 53、Scrophulariaceae 13） | 66 筆歸錯科 | 不可科層級映射，須依屬名逐一 GBIF 查詢 | 🔴 新增 |
| **INCI 與敘述學名矛盾**（115 組） | 物種歸屬錯誤 | 全數進 `conflicts.csv`，人工裁決，未決者標 ambiguous | 🔴 新增 |
| **範圍誤判**（以為 10,000 筆植物，實為 3,862） | 工作量與產出預期落差 | 已重新定義範圍 | 🔴 新增，已解決 |
| 同物異名未統一 | 節點分裂 | 一律使用 GBIF accepted name | ✅ 沿用 |
| LOTUS 覆蓋率不均 | 結論偏向熱門物種 | 「無資料」與「無成分」分開統計；補 CAS→PubChem 第二路徑 | ✅ 強化 |
| 分類系統更新（APG） | 科的歸屬改變 | 記錄 GBIF 擷取日期，每季重跑 | ✅ 沿用 |
| 筆記淹沒 vault | 圖譜不可讀 | 萃取物留資料庫，筆記只寫聚合層級 | ✅ 沿用 |
| 腳本覆蓋人工筆記 | 知識遺失 | AUTO 區塊標記 + git commit | ✅ 沿用 |
| **非植物混入**（藻/菌/地衣 69 筆） | 「植物」結論被污染 | `kingdom` 欄分流，統計時分開 | 🔴 新增 |

---

## 十、驗證方法

每個 Phase 結束時，以下項目必須實際跑過並留下輸出：

**Phase 1**
```bash
python3 _scripts/01_load.py && python3 _scripts/02_clean.py && python3 _scripts/03_parse_taxon.py
```
- `SELECT count(*) FROM ingredient` → 必須是 **13,622**
- `SELECT count(DISTINCT family_accepted) FROM extract` → 應約 200（正規化前為 236）
- `SELECT count(*) FROM extract WHERE family_raw IN ('Palmae','Palmaceae','Arecaceae')` 全部 `family_accepted = 'Arecaceae'`
- `SELECT count(*) FROM extract WHERE family_raw='Laminaceae'` → `family_accepted='Lamiaceae'`
- 屬名解析率 > 98%：`SELECT count(*) FILTER (WHERE genus IS NULL) / count(*) FROM extract`
- `conflicts.csv` 無空白 `resolution` 欄

**Phase 2**
- 隨機抽 20 個物種，手動查 GBIF 網站核對 accepted name 與 family
- `Liliaceae` / `Scrophulariaceae` 原始 66 筆全部有具體 APG IV 科：`SELECT family_raw, family_accepted, count(*) FROM extract WHERE family_raw IN ('Liliaceae','Scrophulariaceae') GROUP BY 1,2`

**Phase 3**
- 抽 30 筆人工核對部位與製程；複合部位（如 `FLOWER/LEAF/STEM EXTRACT`）確實拆成 3 值

**Phase 5**
- 每份報告附上產生它的 SQL 與筆數。看到沒有查詢語句的結論就當它不存在。

**Phase 6**
- 生成後跑 `git diff`，確認 `<!-- AUTO-END -->` 之後的人工區塊零變動
- 斷鏈檢查：所有 wikilink 指向的檔案實際存在

---

## 十一、下一步

1. 建立 vault 目錄結構並 `git init`，`COSING_CAS.csv` 移入 `_data/` 設唯讀
2. 依第三章清單建 `_data/corrections/` 四張對照表（family_typo 15 列、family_apg 約 30 列、taxon_typo 9 列、conflicts 115 列）
3. 寫 `01_load.py` → `03_parse_taxon.py`，跑出第一版 `kb.duckdb`
4. 裁決 `conflicts.csv`（其中 `ROSA RUGOSA` vs `Rosa rubiginosa` 4 筆須優先確認）
5. 進 Phase 2 打 GBIF，優先解決 Liliaceae / Scrophulariaceae 的 66 筆
