# 化粧品成分エクスプローラー

**CosIng 化妝品成分探索器 / Cosmetic Ingredient Explorer**

[English](README.en.md) | [繁體中文](README.md) | 日本語

EU CosIng データベースに登録された 33,638 種類の化粧品成分を探索できる、インタラクティブな知識グラフ + AI 質問応答ツールです。科・種・用途・化合物の関係をひと目で把握でき、自然言語での問い合わせや成分表の分析にも対応しています。

🔗 **[ライブデモ → 517justin.github.io/cosing-explorer](https://517justin.github.io/cosing-explorer/?lang=ja)**（日本語表示で開きます）

## 機能

### 知識グラフ（Explorer）

- **全データ検索** — 33,638 件の成分を即時検索（INCI 名、CAS 番号、説明文、種名、科名、中国語・英語・日本語の通称・和名）
- **力学モデルによる知識グラフ** — Canvas 描画のインタラクティブなグラフ。移動・拡大縮小・クリックでの遷移に対応
- **5 種類のノード** — 科（Family）、用途（Function）、成分（Ingredient）、種（Species）、化合物（Compound）
- **エゴグラフ表示** — ノードをクリックすると周辺ネットワークを展開。パンくずリストで元の画面に戻れます
- **ディープリンク** — URL パラメータで特定の成分・科・種・用途・化合物・検索結果を直接開けます
- **化合物の構造式** — 58,596 件の分子構造 SVG を DecompressionStream でオンデマンド読み込み
- **種の写真** — GBIF Occurrence API から自動取得
- **通称・和名** — 2,827 種と 376 科に中国語・英語の通称、うち 1,575 種と 275 科に和名を収録。検索・表示の両方で利用できます
- **化合物の多言語名称** — 6,581 件の化合物に英語・中国語・日本語の名称と別名を収録（Wikidata 由来）。「caffeine」「槲皮素」「ケルセチン」で検索できます
- **三言語 UI** — 中文 / English / 日本語を切り替え可能。ラベルと通称・和名が言語に合わせて切り替わります
- **絞り込みと並べ替え** — 植物由来 / 規制あり / 構造あり / 用途別 / 科別の絞り込みと、複数の並べ替え
- **規制データ** — EU 化粧品規則 EC 1223/2009 の Annex II–VI を構造化して色分け表示
- **ダークモード** — システム / ライト / ダークの 3 モード
- **完全静的** — バックエンド不要。GitHub Pages にそのままデプロイ

### AI 質問応答（MCP Server + Skill）

- **自然言語での問い合わせ** — Claude Code で「バラ精油の用途は？」「グリセリンの CAS 番号は？」のように質問できます
- **成分表の分析** — 成分表のテキストや写真を渡すと、INCI 名を識別してデータベースを一括照会します
- **規制の即時確認** — 任意の成分の EU 規制区分（Annex II–VI）をすぐに確認できます
- **種・科の情報** — 分類情報、抽出物の一覧、化合物数を照会できます（和名つき）
- **Explorer へのリンク** — すべての回答に知識グラフへのディープリンクを付け、視覚的な探索に進めます

## グラフのノード選択ロジック

各ノードのエゴグラフ（選択したノードを中心に展開される周辺ネットワーク）は、次のルールで隣接ノードを選びます。

### 科（Family）が中心

| 隣接ノード | 選択基準 | 上限 |
|---|---|---|
| 種（Species） | その科に属する成分数の多い順 | 30 |
| 用途（Function） | その科での使用回数の多い順 | 15 |
| 成分（Ingredient） | 上位 15 種それぞれの先頭の成分 | 15 |
| 化合物（Compound） | 含有種の数が多い順 | 20 |

### 用途（Function）が中心

| 隣接ノード | 選択基準 | 上限 |
|---|---|---|
| 科（Family） | その用途を持つ成分数の多い順 | 35 |
| 成分（Ingredient） | 切り替え可：標準 / 規制対象を優先 / 植物由来を優先 | 15 |
| 化合物（Compound） | 関連種の数が多い順 | 15 |

### 成分（Ingredient）が中心

| 隣接ノード | 選択基準 | 上限 |
|---|---|---|
| 用途（Function） | その成分のすべての用途 | すべて |
| 科（Family） | その成分が属する科 | 1 |
| 種（Species） | その成分の由来種 | 1 |
| 関連成分 | 同じ種に由来する他の成分 | 15 |
| 化合物（Compound） | 含有種の数が多い順 | 12 |

### 種（Species）が中心

| 隣接ノード | 選択基準 | 上限 |
|---|---|---|
| 用途（Function） | その種での使用回数の多い順 | 10 |
| 化合物（Compound） | 含有種の数が多い順 | 15 |

### 化合物（Compound）が中心

| 隣接ノード | 選択基準 | 上限 |
|---|---|---|
| 用途（Function） | その化合物を含む種での使用回数の多い順 | 10 |
| 種（Species） | その化合物を含む種の一覧 | 20 |

## ディープリンク

Explorer は URL パラメータに対応しており、外部から特定のページを直接開けます。

| パラメータ | 例 | 説明 |
|-----------|------|------|
| `?ingredient=` | [`?ingredient=87220`](https://517justin.github.io/cosing-explorer/?ingredient=87220&lang=ja) | 特定の成分の知識グラフを開く |
| `?family=` | [`?family=Rosaceae`](https://517justin.github.io/cosing-explorer/?family=Rosaceae&lang=ja) | 特定の科の知識グラフを開く |
| `?species=` | [`?species=Rosa+damascena`](https://517justin.github.io/cosing-explorer/?species=Rosa+damascena&lang=ja) | 特定の種の知識グラフを開く |
| `?function=` | [`?function=SKIN+CONDITIONING`](https://517justin.github.io/cosing-explorer/?function=SKIN+CONDITIONING&lang=ja) | 特定の用途の知識グラフを開く |
| `?compound=` | `?compound=CRPUJAZIXJMDBK-UHFFFAOYSA-N` | 特定の化合物の知識グラフを開く |
| `?search=` | [`?search=lavender`](https://517justin.github.io/cosing-explorer/?search=lavender&lang=ja) | 検索欄に入力済みの状態で結果を表示 |
| `?lang=` | `?lang=ja` / `?lang=en` / `?lang=zh` | 表示言語を指定（他のパラメータと併用可。保存済みの言語設定より優先） |

## AI への質問（Claude Code）

### インストール

```bash
# 1. MCP Server をインストール
cd cosing-mcp && pip install -e .

# 2. Claude Code に追加
claude mcp add cosing-mcp -- cosing-mcp

# 3. 成分分析スキルをインストール（任意）
cp cosing-mcp/skill/cosing-analyze.md .claude/commands/
```

### 成分表の分析

Claude Code で `/cosing-analyze` スキルを使います。

```
/cosing-analyze
AQUA, GLYCERIN, BUTYLENE GLYCOL, ROSA DAMASCENA FLOWER WATER,
PHENOXYETHANOL, CITRIC ACID, SODIUM HYALURONATE
```

成分表の写真をそのまま貼ることもできます。スキルが vision で INCI 名を識別します。日本語で依頼すると、レポートの種名・科名に和名が付き、Explorer のリンクも日本語表示で開きます。

レポートの内容：
- 成分の一覧表（🌿 植物由来 / ⚗️ 合成 / 🔴 使用禁止 / 🟠 使用制限 / ✅ 制限なし）
- 植物由来成分の学名、通称・和名、使用部位、製法
- 規制の詳細（Annex II–VI）
- 未識別の成分と考えられる理由
- 用途の分布
- Explorer グラフへのリンク

### 自然言語での質問

MCP Server は 6 つのツールを提供し、Claude が質問に応じて自動で使い分けます。

| ツール | 説明 | 質問の例 |
|------|------|----------|
| `lookup_ingredient` | 単一成分の照会（INCI / CAS / ref_no） | 「グリセリンとは？」 |
| `search_ingredients` | あいまい検索 + 絞り込み（化合物名・和名にも対応） | 「ラベンダー関連の成分は？」 |
| `get_species` | 種の詳細 + 抽出物の一覧（和名つき） | 「Rosa damascena の抽出物は？」 |
| `get_family` | 科の統計情報（和名つき） | 「シソ科の成分はいくつ？」 |
| `get_regulation` | 規制の照会 | 「フェノキシエタノールの規制は？」 |
| `analyze_ingredient_list` | 成分の一括分析 | `/cosing-analyze` スキルから呼び出し |

## データソース

| データ | 出典 | ライセンス |
|------|------|----------|
| 化粧品成分 | [EU CosIng](https://data.europa.eu/data/datasets/cosing-list-ingredients-and-fragrance-inventory?locale=en)（欧州委員会） | Open Data |
| 分類階層 | [GBIF](https://www.gbif.org/) Backbone Taxonomy | CC BY 4.0 |
| 化合物 | [LOTUS](https://lotus.naturalproducts.net/) Natural Products | CC0 |
| 分子構造 | [PubChem](https://pubchem.ncbi.nlm.nih.gov/) | パブリックドメイン |
| 多言語名称（化合物・種の和名） | [Wikidata](https://www.wikidata.org/) | CC0 |

## アーキテクチャ

```
docs/                        # GitHub Pages のルート（Explorer）
├── index.html               # シングルページアプリ（CSS/JS 埋め込み）
├── data/
│   ├── ingredients.json     # 33,638 件の成分 + インデックス + 通称・和名（約 13 MB）
│   └── compounds.json       # 11,777 件の化合物インデックス（約 6 MB）
└── svg/                     # 631 個の SVG チャンク（約 192 MB）

cosing-mcp/                  # AI 質問応答層（MCP Server）
├── src/cosing_mcp/
│   ├── server.py            # MCP Server のエントリポイント + 6 ツールの定義
│   └── data.py              # GitHub Pages の JSON キャッシュ + メモリ内インデックス
├── tests/                   # 38 件のテスト
├── skill/cosing-analyze.md  # 成分分析スキル（配布用コピー）
└── pyproject.toml           # pip install 設定

.claude/
├── commands/cosing-analyze.md  # Claude Code スキル
└── settings.json               # MCP Server 設定
```

### SVG の圧縮方式

58,596 個の分子構造 SVG は 1 ページに埋め込めません。そこで次の方法を採っています。

1. 冗長な XML 宣言とスタイルを除去
2. gzip 圧縮（レベル 9）
3. Base64 エンコードして 631 個の JSON チャンクに格納
4. ブラウザ側で `DecompressionStream` API により即時展開
5. オンデマンド読み込み — 化合物をクリックしたときにだけ該当チャンクを取得してキャッシュ

## ローカルでの開発

```bash
cd docs
python3 -m http.server 8765
```

ブラウザで `http://localhost:8765` を開きます。

## 再ビルド

元データからサイトを再ビルドする場合：

```bash
# _data/kb.duckdb と _data/structures/ が必要（名称更新には duckdb と opencc-python-reimplemented も必要）
python3 _scripts/build_site.py              # JSON と SVG チャンクをすべて再生成
python3 _scripts/build_site.py --skip-svg   # JSON のみ（docs/svg/ には触れない）
```

多言語名称を更新する場合（Wikidata へ SPARQL クエリを送信。全件で約 20 分）：

```bash
python3 _scripts/20_fetch_wikidata_names.py species    # families / compounds も同様
python3 _scripts/20b_merge_wikidata_names.py            # 既存の通称は上書きせず、不足分のみ補完
```

## ロードマップ

[ROADMAP.md](ROADMAP.md) を参照してください。

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2026-10-02 | Phase 8b-i18n 完了 — Explorer が日本語 UI に対応（中 / EN / 日の三言語切り替え、和名の表示と検索、日本語ヘルプ、`?lang=` パラメータ）、`cosing-analyze` スキルが和名に対応、`README.ja.md` を追加 |
| 2026-10-01 | Phase 8b 完了 — Wikidata 多言語名称：化合物の英/中/日名称と別名（6,581 件）、種の和名 1,575 件・科の和名 275 件、名称検索、MCP での和名対応。ビルドを決定的にし `--skip-svg` を追加 |
| 2026-09-27 | Phase 8a 完了 — RDKit 分子記述子、PubChem CID への直接リンク、化合物ブラウザ（LogP/MW フィルタ）、MCP の記述子フィールド |
| 2026-09-15 | Phase 7 完了 — MCP Server（6 ツール）+ Explorer ディープリンク + cosing-analyze スキル + 31 件のテスト |

## ライセンス

[MIT License](LICENSE) — Chia-Hsiu CHEN
