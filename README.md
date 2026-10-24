# 化妝品成分探索器

**CosIng Cosmetic Ingredient Explorer**

[English](README.en.md) | 繁體中文 | [日本語](README.ja.md)

互動式知識圖譜與 AI 問答，用來探索歐盟 CosIng 資料庫中的 33,638 種化妝品原料。你可以瀏覽科、物種、用途和化合物之間的關係，也能用自然語言查詢，或直接分析成分表。

線上體驗：[517justin.github.io/cosing-explorer](https://517justin.github.io/cosing-explorer/)

## 功能

### 知識圖譜（Explorer）

- 全庫搜尋：33,638 筆原料即時搜尋（INCI 名稱、CAS、描述、物種名、科名、中英文俗名）
- 力導向知識圖譜：用 Canvas 繪製的互動式關聯圖，可以平移、縮放和點擊導航
- 五種節點類型：科（Family）、用途（Function）、原料（Ingredient）、物種（Species）、化合物（Compound）
- Ego-graph 導航：點擊任何節點展開其關聯網絡，可用麵包屑路徑回溯
- 深度連結：支援用 URL 參數直接開啟特定成分、科、物種、用途、化合物或搜尋結果
- 化合物結構式：62,139 個分子結構 SVG 即時載入，以 DecompressionStream 解壓
- 物化性質：化合物面板顯示 9 項 RDKit 描述子（LogP、TPSA、氫鍵供體與受體、可旋轉鍵、環數與芳香環數、重原子數、Fsp3），並直連 PubChem
- 化合物瀏覽：獨立的清單頁，列出被 2 個以上物種報告的 12,375 個化合物，可依 LogP 與分子量範圍篩選、搜尋分子式或名稱、排序與分頁
- 證據與來源：化合物頁會列出所有報告過它的物種（關聯度高的在前），每個物種旁標示 LOTUS 收錄的文獻篇數，並說明有多少只靠 1 篇文獻。物種面板會標明資料來自 LOTUS、在 LOTUS 沒有資料時明說（不代表沒有成分），也列出化合物是透過哪些其他學名（GBIF 同義名、變種）歸入的
- 立體異構物：化合物頁會連到平面結構相同的其他化合物（共有化合物中有 6,201 個至少有一個）
- 物種特有化合物：只在一個物種中被報告的 49,764 個化合物，會在物種與成分面板中按需載入（每次 24 個），點進去可看到完整資料
- 物種照片：透過 GBIF Occurrence API 自動載入實物照片
- 中英文俗名：2,375 種物種有中文俗名、2,448 種有英文俗名，376 科全數附有中英文俗名，搜尋和顯示都支援。日文和名涵蓋 1,587 種物種與 275 科
- 化合物多語名稱：6,815 個化合物附英/中/日名稱與別名（來自 Wikidata），可用「caffeine」「槲皮素」「ケルセチン」搜尋
- 化學角色：7,422 個化合物附 ChEBI 的化學角色（如槲皮素：antioxidant、plant metabolite、chelator），滑過角色可看 ChEBI 的定義。人工整理的對照表再把 33 個角色對應到 29 個 CosIng 用途，面板據此列出「依角色推得的用途」，可點進用途節點；這只是參考，不是 CosIng 的登錄資料
- 三語介面：用按鈕在中文、English、日本語之間切換，介面文字、俗名與和名隨語系變更；日文模式支援和名搜尋（如「ラベンダー」）
- 篩選與排序：植物來源 / 有限制 / 有結構 / 用途 / 科篩選，多種排序模式
- 法規資料：EU 化妝品法規 EC 1223/2009 Annex II–VI 結構化顯示，色彩編碼
- 深色模式：三態主題（系統 / 明 / 暗）
- 純靜態：無後端，GitHub Pages 直接部署

### AI 問答層（MCP Server + Skill）

- 自然語言查詢：在 Claude Code 中直接用中文或英文提問，如「玫瑰精油有哪些用途？」「甘油的 CAS 號是什麼？」
- 成分表分析：貼上成分表文字或照片，自動辨識 INCI 名稱並批次查詢
- 法規速查：即時查詢任何成分的 EU 法規限制狀態（Annex II–VI）
- 物種 / 科資訊：查詢植物分類、萃取物清單、化合物數量；LOTUS 沒有資料的物種會如實回報「沒有資料」，而不是「沒有化合物」
- 化學資訊：查詢成分時，會一併回傳其化合物的分子式、PubChem 連結與描述子，7,281 個有結構的成分都適用；Wikidata 有收錄的，另附多語名稱；ChEBI 有收錄的，另附化學角色與依角色推得的 CosIng 用途
- Explorer 連結：所有查詢結果都附上知識圖譜的深度連結，可以直接開啟視覺化頁面

## 圖譜節點選取邏輯

每種節點的 Ego Graph（以某節點為中心展開的關聯圖）會根據以下規則選取相鄰節點：

### 科（Family）中心

| 相鄰節點類型 | 選取邏輯 | 最大數量 |
|---|---|---|
| 物種（Species） | 按該科下的原料數排序，取最多的物種 | 30 |
| 用途（Function） | 按該科下的原料使用次數排序 | 15 |
| 原料（Ingredient） | 取前 15 個物種各自的第一筆原料 | 15 |
| 化合物（Compound） | 按物種出現數排序，取最常見的化合物 | 20 |

### 用途（Function）中心

| 相鄰節點類型 | 選取邏輯 | 最大數量 |
|---|---|---|
| 科（Family） | 按該用途下的原料數排序 | 35 |
| 原料（Ingredient） | 可切換排序：預設 / 法規限制優先 / 植物來源優先 | 15 |
| 化合物（Compound） | 按關聯物種數排序 | 15 |

### 原料（Ingredient）中心

| 相鄰節點類型 | 選取邏輯 | 最大數量 |
|---|---|---|
| 用途（Function） | 該原料的所有用途 | 全部 |
| 科（Family） | 該原料所屬科 | 1 |
| 物種（Species） | 該原料的來源物種 | 1 |
| 相關原料 | 同物種的其他原料 | 15 |
| 化合物（Compound） | 按物種出現數排序 | 12 |

### 物種（Species）中心

| 相鄰節點類型 | 選取邏輯 | 最大數量 |
|---|---|---|
| 用途（Function） | 按該物種下的原料使用次數排序 | 10 |
| 化合物（Compound） | 按物種出現數排序 | 15 |

### 化合物（Compound）中心

| 相鄰節點類型 | 選取邏輯 | 最大數量 |
|---|---|---|
| 用途（Function） | 按含該化合物物種的用途次數排序 | 10 |
| 物種（Species） | 該化合物出現的物種清單 | 20 |

## 深度連結

Explorer 支援 URL 參數，可從外部直接開啟特定頁面：

| 參數 | 範例 | 說明 |
|------|------|------|
| `?ingredient=` | [`?ingredient=87220`](https://517justin.github.io/cosing-explorer/?ingredient=87220) | 開啟特定成分的知識圖譜 |
| `?family=` | [`?family=Rosaceae`](https://517justin.github.io/cosing-explorer/?family=Rosaceae) | 開啟特定科的知識圖譜 |
| `?species=` | [`?species=Rosa+damascena`](https://517justin.github.io/cosing-explorer/?species=Rosa+damascena) | 開啟特定物種的知識圖譜 |
| `?function=` | [`?function=SKIN+CONDITIONING`](https://517justin.github.io/cosing-explorer/?function=SKIN+CONDITIONING) | 開啟特定用途的知識圖譜 |
| `?compound=` | `?compound=CRPUJAZIXJMDBK-UHFFFAOYSA-N` | 開啟特定化合物的知識圖譜 |
| `?search=` | [`?search=lavender`](https://517justin.github.io/cosing-explorer/?search=lavender) | 預填搜尋框並顯示結果 |
| `?lang=` | [`?lang=ja`](https://517justin.github.io/cosing-explorer/?lang=ja) | 指定介面語言（`zh`／`en`／`ja`），可與其他參數併用，優先於已儲存的語言設定 |

## AI 問答（Claude Code）

### 安裝

```bash
# 1. 安裝 MCP Server
cd cosing-mcp && pip install -e .

# 2. 加入 Claude Code
claude mcp add cosing-mcp -- cosing-mcp

# 3. 安裝成分分析 Skill（可選）
cp cosing-mcp/skill/cosing-analyze.md .claude/commands/
```

### 成分表分析

在 Claude Code 中使用 `/cosing-analyze` skill：

```
/cosing-analyze
AQUA, GLYCERIN, BUTYLENE GLYCOL, ROSA DAMASCENA FLOWER WATER,
PHENOXYETHANOL, CITRIC ACID, SODIUM HYALURONATE
```

也可以直接貼上成分表照片，skill 會用 vision 辨識 INCI 名稱。

分析報告包含：
- 成分總覽表（🌿 植物來源 / ⚗️ 合成 / 🔴 禁用 / 🟠 限制 / ✅ 無限制）
- 植物來源成分的學名、中英文俗名、部位、製程
- 法規限制詳情（Annex II–VI）
- 未識別成分及可能原因
- 用途分布統計
- Explorer 圖譜連結

### 自然語言問答

MCP Server 提供 6 個工具，Claude 會根據問題自動選用：

| 工具 | 說明 | 問法範例 |
|------|------|----------|
| `lookup_ingredient` | 查詢單一成分（INCI / CAS / ref_no） | 「甘油是什麼？」 |
| `search_ingredients` | 模糊搜尋 + 篩選 | 「有哪些薰衣草相關的原料？」 |
| `get_species` | 物種詳情 + 萃取物清單 | 「大馬士革玫瑰有哪些萃取物？」 |
| `get_family` | 科的統計資訊 | 「唇形科有多少種原料？」 |
| `get_regulation` | 法規限制查詢 | 「Phenoxyethanol 的法規限制是什麼？」 |
| `analyze_ingredient_list` | 批次成分分析 | 由 `/cosing-analyze` skill 呼叫 |

## 資料來源

| 資料 | 來源 | 授權 |
|------|------|------|
| 化妝品原料 | [EU CosIng](https://data.europa.eu/data/datasets/cosing-list-ingredients-and-fragrance-inventory?locale=en)（European Commission） | Open Data |
| 分類階層與同義名 | [GBIF](https://www.gbif.org/) Backbone Taxonomy | CC BY 4.0 |
| 化合物 | [LOTUS](https://lotus.naturalproducts.net/) Natural Products | CC0 |
| 分子結構 | [PubChem](https://pubchem.ncbi.nlm.nih.gov/) | Public Domain |
| 多語名稱（化合物、物種和名）、PubChem 沒有的結構 | [Wikidata](https://www.wikidata.org/) | CC0 |
| 化學角色 | [ChEBI](https://www.ebi.ac.uk/chebi/) | CC BY 4.0（需標註） |

## 架構

```
docs/                        # GitHub Pages 根目錄（Explorer）
├── index.html               # 單頁應用（CSS/JS 內嵌，~2,600 行）
├── data/
│   ├── ingredients.json     # 33,638 筆原料 + 索引 + 中英文俗名（~8 MB）
│   ├── compounds.json       # 12,375 筆化合物索引，限 2 個以上物種共有（~6 MB）
│   ├── roles.json           # 735 種 ChEBI 化學角色與對應的 CosIng 用途，化合物以索引引用（~0.1 MB）
│   ├── species_compounds.json  # 完整的物種 → 化合物清單，含文獻篇數（~0.7 MB）
│   └── ingredient_compounds.json  # 另有 5,399 筆化合物，供 MCP Server 使用（~0.8 MB）
├── own/                     # 49,764 個物種特有化合物，分成 180 個按需載入的 chunk（~11 MB）
└── svg/                     # 631 個 SVG chunk（~194 MB）
    └── add/                 # 後來新增的 3,449 個結構圖，共 619 個 chunk（~11 MB）

cosing-mcp/                  # AI 問答層（MCP Server）
├── src/cosing_mcp/
│   ├── server.py            # MCP Server 進入點 + 6 個工具定義
│   └── data.py              # GitHub Pages JSON 快取 + 記憶體索引
├── tests/                   # 48 項測試
├── skill/cosing-analyze.md  # 成分分析 Skill（分發用副本）
└── pyproject.toml           # pip install 設定

.claude/
├── commands/cosing-analyze.md  # Claude Code Skill
└── settings.json               # MCP Server 設定

tests/explorer/              # Explorer 介面與資料測試（Node + jsdom，43 項）
requirements.txt             # _scripts/ 的 Python 依賴
```

### SVG 壓縮策略

62,139 個分子結構 SVG 無法內嵌於單頁，所以建置時先壓縮再切成 chunk：

1. 去除冗餘 XML 宣告與樣式
2. gzip 壓縮（level 9）
3. Base64 編碼存入 631 個 JSON chunk
4. 瀏覽器端以 `DecompressionStream` API 即時解壓
5. 按需載入：使用者點選化合物時才載入對應 chunk 並快取

## 本地開發

```bash
cd docs
python3 -m http.server 8765
```

瀏覽器開啟 `http://localhost:8765`。

## 重新建置

若需從原始資料重建：

```bash
# 首次設定
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 需要 _data/kb.duckdb 與 _data/structures/
.venv/bin/python _scripts/build_site.py              # 重建全部 JSON 與 SVG chunk
.venv/bin/python _scripts/build_site.py --skip-svg   # 只重建 JSON（不動 docs/svg/）
.venv/bin/python _scripts/build_site.py --svg-new-only   # 重建 JSON，並加入尚未發布的結構圖
```

SVG chunk 現在用固定的 gzip 標頭寫出，連續兩次完整建置的結果位元組完全相同。目前已提交的 chunk 仍帶有建置時間戳，所以完整重建會一次改寫全部 631 個檔案。新增化合物後請用 `--svg-new-only`：尚未發布的結構圖會寫進 `docs/svg/add/`，Explorer 在主 chunk 找不到時會讀它，631 個主 chunk 完全不動（完整重建會把 `svg/add/` 併回主 chunk）。其他情況用 `--skip-svg`。

更新 LOTUS 比對（LOTUS 或 GBIF 出新版後）要依序執行 `13b_gbif_synonyms.py`（每個物種的 GBIF 同義名）、`13_lotus.py`、`13c_check_synonyms.py`（向 GBIF 確認每個同義名實際指什麼，會剔除 `Annona glabra` 這類同名異物）、再執行一次 `13_lotus.py`。沒有檢查檔時不會使用任何同義名。

LOTUS 比對（`COSING_SOURCE=2026 .venv/bin/python _scripts/13_lotus.py`）找到新化合物時，建置前要依序執行 `17_fetch_compound_smiles.py`、`17b_wikidata_structures.py`（PubChem 查無的結構，從 Wikidata 取得並以 InChIKey 驗證）、再執行一次 `17_fetch_compound_smiles.py` 以重載 `compound_v2026` 表、`18_render_structures.py`、`19_compute_descriptors.py`。

更新化學角色：從 <https://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.obo.gz> 下載 ChEBI 本體放到 `_data/chebi/`，執行 `.venv/bin/python _scripts/21_load_chebi.py`（以 InChIKey 比對，產生 `compound_roles.json` 與 `roles.json`），再用 `21b_check_role_functions.py` 檢查人工維護的 `_data/chebi/role_function.json`（角色 id 與名稱、用途名稱是否正確，並與 CosIng 自己的標註比對），最後重建網站。

更新多語名稱（會向 Wikidata 發送 SPARQL 查詢，全量約 20 分鐘）：

```bash
.venv/bin/python _scripts/20_fetch_wikidata_names.py species    # families / compounds 同理
.venv/bin/python _scripts/20b_merge_wikidata_names.py            # 只補缺，不覆蓋既有俗名
```

## 測試

```bash
cd cosing-mcp && pip install -e ".[dev]" && pytest       # MCP Server，48 項
cd tests/explorer && npm install && npm test             # Explorer 介面與資料，43 項
```

## 路線圖

見 [ROADMAP.md](ROADMAP.md)。

## 更新紀錄

| 日期 | 內容 |
|------|------|
| 2026-10-24 | Phase 8c 完成：化學角色。從 ChEBI 取得角色，7,422 個化合物有角色（6,703 個以 InChIKey 完全比對，719 個以平面結構比對），共 735 種。化合物面板列出角色與依角色推得的 CosIng 用途，附 ChEBI 授權標示；`lookup_ingredient` 回傳 `chemical_roles` 與 `suggested_cosing_functions`。人工整理的角色→用途對照涵蓋 29 個用途（目標 30 個，沒達到：多出的 `anti-inflammatory agent → SOOTHING` 與 CosIng 的標註只有 1% 吻合，所以拿掉）。對有結構又有推得用途的 771 個成分，CosIng 列出其中至少一個的有 51%。MCP 測試 45 → 48 項、Explorer 36 → 43 項 |
| 2026-10-21 | 處理 LOTUS 問題 6 至 10：LOTUS 以 GBIF 同義名或變種記載的化合物，現在會歸入接受名物種（多 42 個物種有資料、多 4,158 筆報告），但歸入前會先向 GBIF 確認每個名稱的意思，因為 LOTUS 的 960 個同義名中有 637 個其實是獨立的已接受物種（`Annona glabra` 不是 `Annona squamosa`）。化合物頁列出所有報告它的物種（關聯度高的在前），附文獻篇數，並說明 78% 的報告只有 1 篇文獻；物種面板標明來源 LOTUS、沒有資料時明說、並列出歸入時用到的其他學名；平面結構相同的立體異構物互相連結。`get_species` 也回報同樣的資訊 |
| 2026-10-19 | 補回 PubChem 沒有回傳的化合物：原本掉出流程的 1,772 個化合物中，1,768 個現在有來自 Wikidata 的結構（SMILES 必須通過檢查，由它重新計算的 InChIKey 要與 LOTUS 的一致才採用），另有 400 筆回傳時缺 SMILES 的記錄改用 CID 補齊。共有化合物由 11,810 增為 11,978，物種特有化合物由 47,280 增為 48,880，Zingiber officinale 現在列出 713 個化合物，與 LOTUS 的數字相同。新的結構圖放進附加層 `svg/add/`，631 個主 chunk 完全不動 |
| 2026-10-18 | 處理雜交種記號：LOTUS 與 Wikidata 把雜交種寫成帶乘號的 `Rosa × damascena`，使 5 個物種的化合物（包含示範物種 Rosa damascena，現有 75 個化合物）和 16 個物種的 Wikidata 名稱（例如 Citrus limon，現為 レモン 與 檸檬）都對不上。比對時改為忽略乘號。另外抓取並繪製了 94 個新化合物，並新增 `build_site.py --svg-new-only`，只加入新結構圖、不改寫其他 chunk |
| 2026-10-17 | 修正 3 個 LOTUS 顯示問題：物種到化合物的索引每個化合物只留 30 個物種（22.7% 的連結消失，例如 Vitis vinifera 的 352 個共享化合物只顯示 222 個）、成分面板列出點進去是空頁的化合物（188 個成分）、以及只在單一物種出現的 47,219 個化合物完全看不到。Explorer 現在讀取完整的物種清單，物種特有化合物按需載入；`ingredients.json` 從 13 MB 縮到 8 MB，MCP 也改用完整索引計算物種的化合物數 |
| 2026-10-15 | 補上僅供成分使用的化合物名稱：`ingredient_compounds.json` 的 5,411 個化合物中，3,355 個現在附有來自 Wikidata 的英、中、日名稱，MCP Server 可以搜尋。先前因無效而移除的 3 筆物種名稱，也補上了真正的名稱 |
| 2026-10-05 | 技術債清理：MCP Server 現在對全部 7,281 個有結構的成分都能回傳化合物資料（原本只有 1,169 個）、新增建置腳本的 `requirements.txt`、SVG chunk 建置改為確定性、新增 Explorer 測試（Node + jsdom，18 項）、修正窄視窗的工具列排版，並移除 5 筆與學名相同的無效俗名。MCP 測試由 38 項增為 41 項 |
| 2026-10-02 | Phase 8b-i18n 完成：Explorer 日文介面（中／EN／日三語切換、和名顯示與搜尋、日文說明、`?lang=` 參數）、`cosing-analyze` Skill 支援和名、新增 `README.ja.md` |
| 2026-10-01 | Phase 8b 完成：Wikidata 多語名稱，包含化合物 en/zh/ja 名稱與別名（6,581 個）、物種和名 1,575／科和名 275、名稱搜尋、MCP 日文名；建置改為確定性、新增 `--skip-svg`。物種中英文名缺口僅部分縮小（519→457／464→379，Wikidata 無對應俗名） |
| 2026-09-27 | Phase 8a 完成：RDKit 分子描述子、PubChem CID 直連、化合物瀏覽清單頁（LogP/MW 篩選）、MCP 描述子欄位 |
| 2026-09-27 | Phase 8b 至 8d 規劃完成：Wikidata 多語名稱、ChEBI 化學角色、COCONUT 擴充、日文介面 |
| 2026-09-15 | Phase 7 完成：MCP Server 6 個工具、Explorer 深度連結、cosing-analyze Skill 和 31 項測試 |

## 授權

[MIT License](LICENSE)，Chia-Hsiu CHEN
