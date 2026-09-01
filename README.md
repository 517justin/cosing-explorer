# 化妝品成分探索器

**CosIng Cosmetic Ingredient Explorer**

互動式知識圖譜，視覺化探索歐盟 CosIng 資料庫中 33,638 種化妝品原料的關聯——科、物種、用途、化合物一覽無遺。

🔗 **[線上體驗 → 517justin.github.io/cosing-explorer](https://517justin.github.io/cosing-explorer/)**

## 功能

- **全庫搜尋** — 33,638 筆原料即時搜尋（INCI 名稱、CAS、描述、物種名）
- **力導向知識圖譜** — Canvas 繪製的互動式關聯圖，支援平移、縮放、點擊導航
- **五種節點類型** — 科（Family）、用途（Function）、原料（Ingredient）、物種（Species）、化合物（Compound）
- **Ego-graph 導航** — 點擊任何節點展開其關聯網絡，麵包屑路徑可回溯
- **化合物結構式** — 58,596 個分子結構 SVG 即時載入，DecompressionStream 解壓
- **篩選晶片** — 植物來源 / 有限制 / 有結構 / 用途 / 科
- **原料詳情面板** — 描述、法規限制（Annex）、分類階層、化合物縮略圖
- **深色模式** — 三態主題（系統 / 明 / 暗）
- **純靜態** — 無後端，GitHub Pages 直接部署

## 資料來源

| 資料 | 來源 | 授權 |
|------|------|------|
| 化妝品原料 | [EU CosIng](https://data.europa.eu/data/datasets/cosing-list-ingredients-and-fragrance-inventory?locale=en)（European Commission） | Open Data |
| 分類階層 | [GBIF](https://www.gbif.org/) Backbone Taxonomy | CC BY 4.0 |
| 化合物 | [LOTUS](https://lotus.naturalproducts.net/) Natural Products | CC0 |
| 分子結構 | [PubChem](https://pubchem.ncbi.nlm.nih.gov/) | Public Domain |

## 架構

```
docs/                        # GitHub Pages 根目錄
├── index.html               # 單頁應用（CSS/JS 內嵌，~1500 行）
├── data/
│   ├── ingredients.json     # 33,638 筆原料 + 用途索引 + 科索引（13 MB）
│   └── compounds.json       # 11,777 筆化合物索引（5 MB）
└── svg/                     # 631 個 SVG chunk（InChIKey 前兩碼分桶，共 ~192 MB）
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
