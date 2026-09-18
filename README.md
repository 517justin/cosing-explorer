# 化妝品成分探索器

**CosIng Cosmetic Ingredient Explorer**

[English](README.en.md) | 繁體中文

互動式知識圖譜 + AI 問答，探索歐盟 CosIng 資料庫中 33,638 種化妝品原料——科、物種、用途、化合物一覽無遺，還能用自然語言查詢或直接分析成分表。

🔗 **[線上體驗 → 517justin.github.io/cosing-explorer](https://517justin.github.io/cosing-explorer/)**

## 功能

### 知識圖譜（Explorer）

- **全庫搜尋** — 33,638 筆原料即時搜尋（INCI 名稱、CAS、描述、物種名、科名、中英文俗名）
- **力導向知識圖譜** — Canvas 繪製的互動式關聯圖，支援平移、縮放、點擊導航
- **五種節點類型** — 科（Family）、用途（Function）、原料（Ingredient）、物種（Species）、化合物（Compound）
- **Ego-graph 導航** — 點擊任何節點展開其關聯網絡，麵包屑路徑可回溯
- **深度連結** — 支援 URL 參數直接開啟特定成分、科、物種、用途、化合物或搜尋結果
- **化合物結構式** — 58,596 個分子結構 SVG 即時載入，DecompressionStream 解壓
- **物種照片** — 透過 GBIF Occurrence API 自動載入物種實物照片
- **中英文俗名** — 2,827 種物種與 376 科皆附中英文俗名，搜尋與顯示皆支援
- **雙語介面** — 中文／英文切換，所有介面文字與俗名隨語系變更
- **篩選與排序** — 植物來源 / 有限制 / 有結構 / 用途 / 科篩選，多種排序模式
- **法規資料** — EU 化妝品法規 EC 1223/2009 Annex II–VI 結構化顯示，色彩編碼
- **深色模式** — 三態主題（系統 / 明 / 暗）
- **純靜態** — 無後端，GitHub Pages 直接部署

### AI 問答層（MCP Server + Skill）

- **自然語言查詢** — 在 Claude Code 中直接用中文或英文提問，如「玫瑰精油有哪些用途？」「甘油的 CAS 號是什麼？」
- **成分表分析** — 貼上成分表文字或照片，自動辨識 INCI 名稱並批次查詢
- **法規速查** — 即時查詢任何成分的 EU 法規限制狀態（Annex II–VI）
- **物種 / 科資訊** — 查詢植物分類、萃取物清單、化合物數量
- **Explorer 連結** — 所有查詢結果附上知識圖譜的深度連結，一鍵開啟視覺化探索

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
| 分類階層 | [GBIF](https://www.gbif.org/) Backbone Taxonomy | CC BY 4.0 |
| 化合物 | [LOTUS](https://lotus.naturalproducts.net/) Natural Products | CC0 |
| 分子結構 | [PubChem](https://pubchem.ncbi.nlm.nih.gov/) | Public Domain |

## 架構

```
docs/                        # GitHub Pages 根目錄（Explorer）
├── index.html               # 單頁應用（CSS/JS 內嵌，~2,000 行）
├── data/
│   ├── ingredients.json     # 33,638 筆原料 + 索引 + 中英文俗名（~13 MB）
│   └── compounds.json       # 11,777 筆化合物索引（~5 MB）
└── svg/                     # 631 個 SVG chunk（~192 MB）

cosing-mcp/                  # AI 問答層（MCP Server）
├── src/cosing_mcp/
│   ├── server.py            # MCP Server 進入點 + 6 個工具定義
│   └── data.py              # GitHub Pages JSON 快取 + 記憶體索引
├── tests/                   # 31 項測試
├── skill/cosing-analyze.md  # 成分分析 Skill（分發用副本）
└── pyproject.toml           # pip install 設定

.claude/
├── commands/cosing-analyze.md  # Claude Code Skill
└── settings.json               # MCP Server 設定
```

### SVG 壓縮策略

58,596 個分子結構 SVG 無法內嵌於單頁。解法：

1. 去除冗餘 XML 宣告與樣式
2. gzip 壓縮（level 9）
3. Base64 編碼存入 631 個 JSON chunk
4. 瀏覽器端以 `DecompressionStream` API 即時解壓
5. 按需載入 — 使用者點選化合物時才載入對應 chunk 並快取

## 本地開發

```bash
cd docs
python3 -m http.server 8765
```

瀏覽器開啟 `http://localhost:8765`。

## 重新建置

若需從原始資料重建：

```bash
# 需要 _data/kb.duckdb 與 _data/structures/
python3 _scripts/build_site.py
```

## 授權

[MIT License](LICENSE) — Chia-Hsiu CHEN
