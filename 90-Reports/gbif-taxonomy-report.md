# Phase 2 — GBIF 分類階層報告

- 不重複二名法：**1263**，成功解析 **1193**（94.5%）
- 其中 GBIF 判定為同物異名並統一到接受名：**185**
- 模糊比對（matchType=FUZZY）：**17**，需抽查
- 種層級查無、退回屬層級取科：**55**
- 萃取物有科別者：**3862 / 3862**（100.00%）

## 一、APG IV 拆分科的判定結果

這些科在 APG IV 被拆開，無法在科層級映射，由 GBIF 依屬名逐一判定。

| COSING 原科名 | GBIF 判定 | 列數 |
| --- | --- | --- |
| Liliaceae | Asphodelaceae | 18 |
| Liliaceae | Asparagaceae | 17 |
| Liliaceae | Amaryllidaceae | 9 |
| Liliaceae | Liliaceae | 7 |
| Liliaceae | Smilacaceae | 2 |
| Myoporaceae | Scrophulariaceae | 1 |
| Scrophulariaceae | Scrophulariaceae | 7 |
| Scrophulariaceae | Plantaginaceae | 4 |
| Scrophulariaceae | Orobanchaceae | 2 |

## 二、COSING 科名與 GBIF 不一致者

以 GBIF 為準（`family_final`），但原值保留於 `family_accepted` 可查。

| COSING（正規化後） | GBIF | 列數 |
| --- | --- | --- |
| Nymphaeaceae | Nelumbonaceae | 20 |
| Saxifragaceae | Grossulariaceae | 17 |
| Caprifoliaceae | Viburnaceae | 14 |
| Verbenaceae | Lamiaceae | 11 |
| Pinaceae | Cupressaceae | 9 |
| Ranunculaceae | Paeoniaceae | 8 |
| Euphorbiaceae | Phyllanthaceae | 8 |
| Asparagaceae | Amaryllidaceae | 8 |
| Buxaceae | Simmondsiaceae | 6 |
| Hypericaceae | Clusiaceae | 6 |
| Araceae | Acoraceae | 5 |
| Amaryllidaceae | Asparagaceae | 5 |
| Usneaceae | Parmeliaceae | 5 |
| Saxifragaceae | Hydrangeaceae | 5 |
| Polyporaceae | Fomitopsidaceae | 4 |
| Adoxaceae | Viburnaceae | 4 |
| Loranthaceae | Viscaceae | 4 |
| Rosaceae | Quillajaceae | 4 |
| Hamamelidaceae | Altingiaceae | 4 |
| Oocystaceae | Chlorellaceae | 3 |
| Polypodiaceae | Dryopteridaceae | 2 |
| Cyperaceae | Ulvaceae | 2 |
| Loganiaceae | Scrophulariaceae | 2 |
| Verbenaceae | Oleaceae | 2 |
| Polypodiaceae | Pteridaceae | 2 |
| Boraginaceae | Namaceae | 2 |
| Clusiaceae | Calophyllaceae | 2 |
| Cyatheaceae | Cibotiaceae | 1 |
| Gelidiaceae | Plocamiaceae | 1 |
| Hypneaceae | Cystocloniaceae | 1 |
| Aristolochiaceae | Ceramiaceae | 1 |
| Simaroubaceae | Irvingiaceae | 1 |
| Gelidiaceae | Gelidiellaceae | 1 |
| Salicaceae | Achariaceae | 1 |
| Clusiaceae | Hypericaceae | 1 |
| Theaceae | Anacardiaceae | 1 |
| Porphyridaceae | Porphyridiaceae | 1 |
| Fabaceae | Asteraceae | 1 |
| Gigartinaceae | Phyllophoraceae | 1 |
| Olacaceae | Ximeniaceae | 1 |
| Rhodymeniaceae | Palmariaceae | 1 |
| Hypericaceae | Calophyllaceae | 1 |

## 三、生物界別分布

資料集名為「植物」萃取物，實際含藻類、真菌與地衣。統計時須分流，否則「植物」結論會被污染。

| kingdom | 列數 |
| --- | --- |
| Plantae | 3782 |
| (未定) | 36 |
| Chromista | 23 |
| Fungi | 21 |

## 四、需人工抽查者

| 類型 | 筆數 | 說明 |
| --- | --- | --- |
| FUZZY 且改變種小名 ⚠️ | 15 | 最高風險：既猜拼字又跟了同物異名 |
| FUZZY 比對（全部） | 17 | GBIF 靠模糊比對命中，拼字與原文不同 |
| 屬層級退回 | 55 | 種名查無，僅取到屬與科 |
| 完全查無 | 15 | 無科別，不進入圖譜 |

### FUZZY 且改變種小名的逐筆清單

| COSING 寫法 | GBIF 接受名 | 信心 |
| --- | --- | --- |
| Carapa guaianensis | Carapa guianensis | 93 |
| Origanum cretium | Origanum creticum | 93 |
| Terminalia bellerica | Terminalia bellirica | 93 |
| Vetiveria zizanoides | Vetiveria zizanioides | 93 |
| Boswellia carterii | Boswellia sacra | 94 |
| Commiphora erythrea | Commiphora kataf | 94 |
| Dacrydium franklini | Lagarostrobos franklinii | 95 |
| Thaumatococcus danielli | Thaumatococcus daniellii | 95 |
| Thymus serpillum | Thymus serpyllum | 95 |
| Camellia kissi | Camellia kissii | 96 |
| Citrus aurantifolia | Citrus aurantiifolia | 96 |
| Magnolia liliflora | Magnolia liliiflora | 96 |
| Narcissus pseudo-narcissus | Narcissus pseudonarcissus | 96 |
| Nuphar luteum | Nuphar lutea | 96 |
| Santalum spicata | Santalum spicatum | 96 |

## 五、驗收檢查

| 檢查項 | 結果 |
| --- | --- |
| 每個生物來源列都有科別 | ✅ 通過 |
| APG IV 拆分科全數判定完畢（0 筆待決） | ✅ 通過 |
| 物種解析率 > 90% | ✅ 通過 |
| 同物異名已統一到接受名 | ✅ 通過 |
| 科名不一致者全部留有紀錄 | ✅ 通過 |
| 無動物界誤配 | ✅ 通過 |
