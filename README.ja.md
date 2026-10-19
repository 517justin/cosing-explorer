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
- **化合物の構造式** — 60,858 件の分子構造 SVG を DecompressionStream でオンデマンド読み込み
- **一つの種に固有の化合物** — 単一の種でのみ報告された 48,880 件の化合物を、種・成分パネルで必要なときに 24 件ずつ読み込み、詳細も表示できます
- **物理化学的性質** — 化合物パネルに RDKit の記述子 9 項目（LogP、TPSA、水素結合供与体・受容体、回転可能結合、環数と芳香環数、重原子数、Fsp3）を表示し、PubChem へ直接リンク
- **化合物ブラウザ** — 2 種以上の種で報告された 11,978 件の化合物を一覧表示する専用画面。LogP と分子量の範囲での絞り込み、分子式・名前での検索、並べ替え、ページ送りに対応
- **種の写真** — GBIF Occurrence API から自動取得
- **通称・和名** — 中国語の通称は 2,375 種、英語の通称は 2,448 種に、376 科すべてに中国語・英語の通称を収録。和名は 1,587 種と 275 科に収録しています。検索・表示の両方で利用できます
- **化合物の多言語名称** — 6,644 件の化合物に英語・中国語・日本語の名称と別名を収録（Wikidata 由来）。「caffeine」「槲皮素」「ケルセチン」で検索できます
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
- **化学データ** — 成分を照会すると、その化合物の分子式、PubChem リンク、記述子も返します。構造を持つ 7,281 成分すべてが対象で、Wikidata に収録があれば多言語名称も付きます
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
│   ├── ingredients.json     # 33,638 件の成分 + インデックス + 通称・和名（約 8 MB）
│   ├── compounds.json       # 11,978 件の化合物インデックス。2 種以上に共通するもの（約 6 MB）
│   ├── species_compounds.json  # 種 → 化合物の完全なリスト（約 0.4 MB）
│   └── ingredient_compounds.json  # MCP Server 用の追加 5,411 件の化合物（約 0.8 MB）
├── own/                     # 種に固有の 48,880 件の化合物。必要時に読み込む 178 チャンク（約 11 MB）
└── svg/                     # 631 個の SVG チャンク（約 194 MB）
    └── add/                 # 後から追加した 2,168 件の構造式、583 チャンク（約 7 MB）

cosing-mcp/                  # AI 質問応答層（MCP Server）
├── src/cosing_mcp/
│   ├── server.py            # MCP Server のエントリポイント + 6 ツールの定義
│   └── data.py              # GitHub Pages の JSON キャッシュ + メモリ内インデックス
├── tests/                   # 43 件のテスト
├── skill/cosing-analyze.md  # 成分分析スキル（配布用コピー）
└── pyproject.toml           # pip install 設定

.claude/
├── commands/cosing-analyze.md  # Claude Code スキル
└── settings.json               # MCP Server 設定

tests/explorer/              # Explorer の UI とデータのテスト（Node + jsdom、28 件）
requirements.txt             # _scripts/ 用の Python 依存パッケージ
```

### SVG の圧縮方式

60,858 個の分子構造 SVG は 1 ページに埋め込めません。そこで次の方法を採っています。

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
# 初回のみ
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# _data/kb.duckdb と _data/structures/ が必要
.venv/bin/python _scripts/build_site.py              # JSON と SVG チャンクをすべて再生成
.venv/bin/python _scripts/build_site.py --skip-svg   # JSON のみ（docs/svg/ には触れない）
.venv/bin/python _scripts/build_site.py --svg-new-only   # JSON と、未公開の構造式のみ追加
```

SVG チャンクは gzip ヘッダーを固定して書き出すため、完全ビルドを繰り返しても結果はバイト単位で一致します。ただし、これまでにコミット済みのチャンクにはビルド時刻が入っているため、完全ビルドでは 631 ファイルすべてが一度だけ書き換わります。化合物を追加したときは `--svg-new-only` を使ってください。未公開の構造式は `docs/svg/add/` に書き出され、Explorer はメインのチャンクに無いときにそこを読みます（631 個のメインチャンクは変わりません。完全ビルドでは `svg/add/` がメインに統合されます）。それ以外は `--skip-svg` を使ってください。

LOTUS の照合（`COSING_SOURCE=2026 .venv/bin/python _scripts/13_lotus.py`）で新しい化合物が見つかったら、ビルドの前に `17_fetch_compound_smiles.py`、`17b_wikidata_structures.py`（PubChem に無い構造式を Wikidata から取得し InChIKey で検証）、`17_fetch_compound_smiles.py`（`compound_v2026` の再読み込み）、`18_render_structures.py`、`19_compute_descriptors.py` を順に実行してください。

多言語名称を更新する場合（Wikidata へ SPARQL クエリを送信。全件で約 20 分）：

```bash
.venv/bin/python _scripts/20_fetch_wikidata_names.py species    # families / compounds も同様
.venv/bin/python _scripts/20b_merge_wikidata_names.py            # 既存の通称は上書きせず、不足分のみ補完
```

## テスト

```bash
cd cosing-mcp && pip install -e ".[dev]" && pytest       # MCP Server、43 件
cd tests/explorer && npm install && npm test             # Explorer の UI とデータ、28 件
```

## ロードマップ

[ROADMAP.md](ROADMAP.md) を参照してください。

## 更新履歴

| 日付 | 内容 |
|------|------|
| 2026-10-19 | PubChem が返さなかった化合物を回収 — パイプラインから脱落していた 1,772 件のうち 1,768 件に Wikidata 由来の構造式を付与（SMILES から再計算した InChIKey が LOTUS のキーと一致した場合のみ採用）、SMILES なしで返ってきた 400 件は CID で補完。共通化合物は 11,810 から 11,978 件、種に固有の化合物は 47,280 から 48,880 件に増え、Zingiber officinale は LOTUS と同じ 713 件になりました。新しい構造式は追加レイヤー `svg/add/` に置き、631 個のメインチャンクには触れません |
| 2026-10-18 | 交雑種記号の処理 — LOTUS と Wikidata は交雑種を乗算記号付き（`Rosa × damascena`）で表記するため、5 種の化合物（デモ用の Rosa damascena を含み、現在 75 件）と 16 種の Wikidata 名称（例：Citrus limon は現在 レモン・檸檬）が一致していませんでした。比較時に記号を無視するようにしました。新しい化合物 94 件を取得して描画し、既存チャンクを書き換えずに構造式を追加する `build_site.py --svg-new-only` を追加 |
| 2026-10-17 | LOTUS の表示問題を 3 件修正 — 種から化合物へのインデックスが化合物ごとに 30 種で切られていた（リンクの 22.7% が欠落。例：Vitis vinifera は共通化合物 352 件のうち 222 件しか表示されなかった）、成分パネルが開いても空のページになる化合物を列挙していた（188 成分）、単一の種にしか現れない 47,219 件の化合物がまったく見えなかった。Explorer は完全な種リストを読み込み、種に固有の化合物は必要時に読み込みます。`ingredients.json` は 13 MB から 8 MB に縮小し、MCP も完全なインデックスで種の化合物数を数えます |
| 2026-10-15 | 成分専用の化合物の名称を追加 — `ingredient_compounds.json` の 5,411 件のうち 3,355 件に Wikidata 由来の英語・中国語・日本語名を付け、MCP Server で検索可能に。無効として削除していた種名 3 件も、正しい名称で補完 |
| 2026-10-05 | 技術的負債の解消 — MCP Server が構造を持つ全 7,281 成分の化合物データを返せるように（従来は 1,169 件）、ビルドスクリプト用の `requirements.txt`、SVG チャンク生成の決定性、Explorer のテスト（Node + jsdom、18 件）、狭いウィンドウでのツールバー表示の修正、学名と同じ無効な通称 5 件の削除。MCP のテストは 38 件から 41 件に |
| 2026-10-02 | Phase 8b-i18n 完了 — Explorer が日本語 UI に対応（中 / EN / 日の三言語切り替え、和名の表示と検索、日本語ヘルプ、`?lang=` パラメータ）、`cosing-analyze` スキルが和名に対応、`README.ja.md` を追加 |
| 2026-10-01 | Phase 8b 完了 — Wikidata 多言語名称：化合物の英/中/日名称と別名（6,581 件）、種の和名 1,575 件・科の和名 275 件、名称検索、MCP での和名対応。ビルドを決定的にし `--skip-svg` を追加 |
| 2026-09-27 | Phase 8a 完了 — RDKit 分子記述子、PubChem CID への直接リンク、化合物ブラウザ（LogP/MW フィルタ）、MCP の記述子フィールド |
| 2026-09-15 | Phase 7 完了 — MCP Server（6 ツール）+ Explorer ディープリンク + cosing-analyze スキル + 31 件のテスト |

## ライセンス

[MIT License](LICENSE) — Chia-Hsiu CHEN
