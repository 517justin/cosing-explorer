# Roadmap

## Phase 8 — 分子知識圖譜擴充 Molecular Knowledge Graph Expansion

### 8a — 分子描述子 + PubChem 連結（短期 ~1 week）✅ 已完成 2026-09-27

**目標：** 在 Explorer 化合物面板中顯示物化性質，並提供 PubChem 外部連結。

| 工作項 | 說明 | 狀態 |
|--------|------|------|
| `19_compute_descriptors.py` | RDKit 計算 9 項描述子（LogP, TPSA, HBD, HBA, rotatable bonds, rings, aromatic rings, heavy atoms, fsp3），58,596 化合物零失敗，約 52 秒 | ✅ |
| `build_site.py` 修改 | CID + MW + 描述子匯出至 `compounds.json`（5.0→5.6 MB，PubChem CID 已有 58,996 筆，零 API 呼叫） | ✅ |
| Explorer UI | 化合物面板顯示描述子表格 + PubChem CID 直連 | ✅ |
| Explorer UI | 獨立「化合物瀏覽」清單頁：LogP/MW 範圍篩選、分子式/名稱搜尋、排序（物種數/MW/LogP）、分頁（規劃時原定滑桿，實作時發現無清單視圖可掛，改為新建清單頁） | ✅ |
| MCP Server | `lookup_ingredient` 回傳 `compound` 欄位（formula, IUPAC, MW, CID, PubChem URL, descriptors） | ✅ |

**前提：** 無 — 所有資料已在磁碟上。

**驗收：**
- ✅ 化合物面板顯示 MW, LogP, TPSA, HBD/HBA, rings
- ✅ PubChem 連結使用 CID 直連（`/compound/{cid}`），無 CID 時退回關鍵字搜尋
- ✅ 化合物瀏覽頁篩選器正常運作（LogP 2–5 → 11,777 縮至 4,814 筆）
- ✅ `compounds.json` 5.60 MB（< 8 MB）
- ✅ MCP 測試 31→33 項全過

**副產出：**
- 修正既有手機版 toolbar 溢出 bug（新增按鈕觸發，非本次目標但一併修好）✅
- 修正 `build_site.py` 重跑會清空手動維護的 `sp_zh`/`sp_en`/`fam_zh`/`fam_en` 問題 ✅ —— 已將 4 個字典抽出至 `_data/common_names.json`（source of truth，人工維護），`build_site.py` 現在從此檔案讀入並合併進輸出，重跑不再清空俗名。Phase 8b 新增 `sp_ja`/`fam_ja` 時可直接加進同一個檔案

---

### 8b — Wikidata 多語名稱 + 物種名稱補缺（中期 2–4 weeks）✅ 已完成 2026-10-01（物種缺口驗收未達，見下）

**目標：** 從 Wikidata 取得化合物與物種的多語系名稱（en/zh/ja/ko），填補物種中英文名缺口。

| 工作項 | 說明 | 狀態 |
|--------|------|------|
| `20_fetch_wikidata_names.py` | SPARQL 批次查詢（P235 InChIKey／P225 學名）→ labels + aliases（+ P1843 俗名），≤50 key/query、2s 間隔、可續跑快取於 `_data/wikidata/`。物種 2,772/2,827、科 376/376、化合物 11,541/11,777 有 Wikidata 條目，零失敗、未觸發 rate limit | ✅ |
| `20b_merge_wikidata_names.py` | 合併至 `_data/common_names.json`（只補缺、不覆蓋人工整理）與新檔 `_data/compound_names.json`；簡體以 OpenCC `s2twp` 轉繁體；過濾系統命名（IUPAC 式）與與學名相同的標籤 | ✅ |
| 物種名稱補缺 | 缺中文 519 → 457、缺英文 464 → 379；新增 `sp_ja` 1,575、`fam_ja` 275 | ⚠️ 部分（見下） |
| `build_site.py` 修改 | 匯出 `sp_ja`、`fam_ja`、化合物 `nm`（en ≤3、zh ≤4、ja ≤5）；`compounds.json` 5.60→5.96 MB。另加 `--skip-svg`（只重建 JSON、不動 631 個 SVG chunk）與函數／科排序 tie-breaker（重建結果位元組一致） | ✅ |
| Explorer 搜尋 | 支援化合物名稱（en/zh/ja）；化合物結果固定保留最多 5 個名額；化合物瀏覽頁的名稱欄與搜尋同步支援 | ✅ |
| Explorer 面板 | 化合物面板顯示 `caffeine \| 咖啡因 \| カフェイン` 與別名 | ✅ |
| MCP Server | `lookup_ingredient` 回傳 `compound.names`；`search_ingredients` 可用化合物名稱／日文和名搜尋；`get_species`／`get_family`／`lookup_ingredient` 回傳日文名；測試 33→38 項 | ✅ |

**前提：** Phase 8a 完成。

**驗收：**
- ✅ 搜尋 "caffeine" → 化合物節點（亦可用「咖啡因」「槲皮素」「ケルセチン」）
- ✅ 化合物面板顯示 "caffeine | 咖啡因 | カフェイン"（原訂範例為 "咖啡鹼"；Wikidata 主名為「咖啡因」，「咖啡鹼」列為別名）
- ❌ 物種缺中文名 519 → <100：實得 457。缺英文名 464 → <50：實得 379。**原因：** 剩餘缺口絕大多數是 Wikidata 上有條目、但英文標籤只是學名（360 筆），或根本沒有條目（19 筆）——這些物種在 Wikidata 沒有俗名可取，目標在資料源上不可達
- ✅ SPARQL rate limit 遵守（≤50 key/query、2s 間隔、帶 User-Agent，全程無 429）

**化合物名稱覆蓋：** 6,581 / 11,777 有至少一個名稱（en 6,387、zh 1,874、ja 1,635）；其餘多為無俗名的衍生物，維持以分子式／IUPAC 顯示。

**未做／後續選項：**
- CID fallback 查詢：以 InChIKey 即已 98% 命中（僅 236 個未命中），暫無必要
- 韓文（ko）已抓入原始快取但未匯出（目前無介面使用）
- 物種缺口若要再縮小：GBIF vernacular names 補充、或人工／LLM 輔助翻譯
- 化合物名稱僅涵蓋 Explorer 的 11,777 個；全 58,996 需 `20_fetch_wikidata_names.py compounds --all`（以本次約 3 秒／批估算約 1 小時）
- 日文介面本身屬 8b-i18n，尚未實作（資料層 `sp_ja`／`fam_ja` 已就緒）

---

### 8b-i18n — 日文介面 Japanese UI（中期，與 8b 同次 PR）

**目標：** 將 Explorer 從雙語（中/英）擴充為三語（中/英/日），利用 8b 產出的日文名稱資料。

| 工作項 | 說明 |
|--------|------|
| `I18N.ja` 字典 | ~60 key 日文翻譯（title: '化粧品成分エクスプローラー' 等） |
| `setLang()` 三語切換 | 語言按鈕循環 中 → EN → 日 → 中；localStorage 記住選擇 |
| `spName()` / `famName()` | 加 `ja` 分支，讀取 `D.sp_ja` / `D.fam_ja` |
| `renderHelp()` 日文版 | ~30 行說明文字翻譯（節點類型、操作方式、法規分類） |
| 搜尋擴充 | `setupSearch()` 加 `D.sp_ja` 比對（「ラベンダー」→ *Lavandula angustifolia*） |
| HTML/Meta | `document.documentElement.lang = 'ja'`、`<title>` 切換 |
| MCP Server | `data.py` 加 `sp_ja` / `fam_ja` dict |
| cosing-analyze Skill | 若用戶語言為日文，報告中顯示和名 |
| `README.ja.md` | 日文版專案說明 |
| 測試 | `conftest.py` 補日文 fixture 樣本 |

**前提：** Phase 8b 完成（`sp_ja` / `fam_ja` 資料已匯出）。

**驗收：**
- 語言切換按鈕在三語間正確循環
- 日文模式下物種/科顯示和名
- 搜尋日文和名可找到對應物種
- Help 說明完整顯示日文
- `README.ja.md` 與中英文版結構一致

---

### 8c — ChEBI 化學角色（中期 2–4 weeks，可與 8b 平行）

**目標：** 從 ChEBI 引入化學角色標註，解釋化合物為什麼具有特定用途。

| 工作項 | 說明 |
|--------|------|
| `21_load_chebi.py` | 下載 ChEBI TSV + 角色本體，以 InChIKey 比對（預估 ~3,000–5,000 overlap） |
| 角色→用途對照表 | 建立 ChEBI role ↔ CosIng function 交叉映射（~40 組，半自動） |
| `build_site.py` 修改 | `compounds.json` 加 `chemical_roles` 陣列 |
| Explorer UI | 化合物面板顯示化學角色 |
| MCP Server | 新增或擴充工具：查詢化合物角色 + role→function mapping |

**前提：** Phase 8a 完成。  
**授權：** ChEBI CC BY 4.0，需標註。

**驗收：**
- 化合物面板顯示角色（如 quercetin: "plant metabolite, antioxidant"）
- Role ↔ Function 覆蓋 ≥30 / 82 用途
- ≥3,000 化合物有角色標註
- ChEBI 授權標示正確

---

### 8d — COCONUT 天然物擴充（長期 1–2 months）

**目標：** 從 COCONUT 資料庫補充化合物—物種關聯，提高物種覆蓋率。

| 工作項 | 說明 |
|--------|------|
| COCONUT 評估 | 下載 COCONUT，分析與 LOTUS 重疊度，GBIF 學名對齊品質 |
| `22_load_coconut.py` | 解析、去重、對齊 GBIF 接受名，插入新 compound-species pairs |
| PubChem 批次 fetch | 為新 InChIKey 取得 SMILES/CID（可能 200K+ 新化合物，rate-limited） |
| RDKit SVG 渲染 | 新化合物結構圖（可能 100K+ 新檔案，~500 MB） |
| Explorer 架構 | 決定方案：提高 ≥2 threshold / lazy-load 化合物詳情 / 依科分拆 JSON |
| 描述子 + 名稱回填 | 為新化合物計算描述子、取 Wikidata 名稱 |
| 全流程重建 | 完整 pipeline rebuild + 回歸測試 + Explorer 效能驗證 |

**前提：** Phase 8a–8c 穩定。  
**授權：** COCONUT MIT。

**驗收：**
- 無化合物物種從 608 降至 <200
- Explorer 載入時間 <5s（4G 網路）
- LOTUS + COCONUT 無重複 compound-species pairs
- 物種名稱 GBIF 對齊率 >90%
- SVG chunks 符合 GitHub Pages 100MB/file 限制

---

## 已完成 Completed

| Phase | 說明 | 完成日期 |
|-------|------|----------|
| Phase 0–3 | 資料清洗、分類對齊、GBIF 驗證 | 2026-09 |
| Phase 4 | LOTUS 化合物富集 + PubChem CAS 查詢 | 2026-09 |
| Phase 5 | 法規層 Annex II–VI | 2026-09 |
| Phase 6 | Explorer 知識圖譜 SPA + 物種照片 + 俗名 | 2026-09 |
| Phase 7 | MCP Server + 深度連結 + cosing-analyze Skill | 2026-09-15 |
| Phase 8a | RDKit 分子描述子 + PubChem 直連 + 化合物瀏覽頁 | 2026-09-27 |
| Phase 8b | Wikidata 多語名稱（化合物 en/zh/ja、物種／科和名）+ 名稱搜尋 | 2026-10-01 |
