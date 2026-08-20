# Phase 2 — GBIF 分類階層報告

- 不重複二名法：**3179**，成功解析 **3009**（94.7%）
- 其中 GBIF 判定為同物異名並統一到接受名：**540**
- 模糊比對（matchType=FUZZY）：**54**，需抽查
- 種層級查無、退回屬層級取科：**116**
- 萃取物有科別者：**7690 / 7690**（100.00%）

## 一、APG IV 拆分科的判定結果

這些科在 APG IV 被拆開，無法在科層級映射，由 GBIF 依屬名逐一判定。

| COSING 原科名 | GBIF 判定 | 列數 |
| --- | --- | --- |
| Liliaceae | Liliaceae | 34 |
| Liliaceae | Asparagaceae | 29 |
| Liliaceae | Asphodelaceae | 23 |
| Liliaceae | Amaryllidaceae | 14 |
| Liliaceae | Smilacaceae | 3 |
| Liliaceae | Colchicaceae | 1 |
| Myoporaceae | Scrophulariaceae | 1 |
| Scrophulariaceae | Scrophulariaceae | 15 |
| Scrophulariaceae | Plantaginaceae | 7 |
| Scrophulariaceae | Paulowniaceae | 3 |
| Scrophulariaceae | Rehmanniaceae | 3 |
| Scrophulariaceae | Orobanchaceae | 2 |
| Scrophulariaceae | Linderniaceae | 1 |

## 二、COSING 科名與 GBIF 不一致者

以 GBIF 為準（`family_final`），但原值保留於 `family_accepted` 可查。

| COSING（正規化後） | GBIF | 列數 |
| --- | --- | --- |
| Nymphaeaceae | Nelumbonaceae | 20 |
| Saxifragaceae | Grossulariaceae | 19 |
| Caprifoliaceae | Viburnaceae | 15 |
| Ranunculaceae | Paeoniaceae | 15 |
| Verbenaceae | Lamiaceae | 11 |
| Asparagaceae | Amaryllidaceae | 10 |
| Adoxaceae | Viburnaceae | 9 |
| Hypericaceae | Clusiaceae | 9 |
| Pinaceae | Cupressaceae | 8 |
| Euphorbiaceae | Phyllanthaceae | 8 |
| Buxaceae | Simmondsiaceae | 7 |
| Saxifragaceae | Hydrangeaceae | 7 |
| Araceae | Acoraceae | 6 |
| Usneaceae | Parmeliaceae | 5 |
| Empetraceae | Ericaceae | 5 |
| Phormiaceae | Asphodelaceae | 4 |
| Hamamelidaceae | Altingiaceae | 4 |
| Rosaceae | Quillajaceae | 4 |
| Ganodermataceae | Polyporaceae | 4 |
| Polyporaceae | Fomitopsidaceae | 4 |
| Amaryllidaceae | Asparagaceae | 4 |
| Oocystaceae | Chlorellaceae | 4 |
| Mangnoliaceae | Magnoliaceae | 3 |
| Salicaceae | Achariaceae | 3 |
| Hypericaceae | Calophyllaceae | 3 |
| Stephanosphaeraceae | Haematococcaceae | 3 |
| Polypodiaceae | Pteridaceae | 3 |
| Loranthaceae | Viscaceae | 3 |
| Alliaceae | Amaryllidaceae | 3 |
| Loganiaceae | Scrophulariaceae | 3 |
| Boraginaceae | Cordiaceae | 3 |
| Aloeaceae | Asphodelaceae | 3 |
| Theaceae | Brassicaceae | 2 |
| Salicaceae | Polyporaceae | 2 |
| Buddlejaceae | Scrophulariaceae | 2 |
| Dryoptiridaceae | Dryopteridaceae | 2 |
| Olacaceae | Ximeniaceae | 2 |
| Astaraceae | Asteraceae | 2 |
| Verbenaceae | Oleaceae | 2 |
| Phormidiaceae | Microcoleaceae | 2 |
| Rhodymeniaceae | Palmariaceae | 2 |
| Cyperaceae | Ulvaceae | 2 |
| Santalaceae | Viscaceae | 2 |
| Sapindaceae | Caryophyllaceae | 2 |
| Fucaceae | Sargassaceae | 2 |
| Polypodiaceae | Dryopteridaceae | 2 |
| Meripilaceae | Grifolaceae | 2 |
| Rhizopodaceae | Poaceae | 2 |
| Soleriaceae | Solieriaceae | 2 |
| Porphyridaceae | Porphyridiaceae | 2 |
| Phanerochaetaceae | Irpicaceae | 2 |
| Rhodellaceae | Crassulaceae | 2 |
| Casaurinaceae | Casuarinaceae | 2 |
| Aristolochiaceae | Ceramiaceae | 2 |
| Polyporaceae | Grifolaceae | 2 |
| Melianthaceae | Francoaceae | 2 |
| Fabaceae | Cordycipitaceae | 2 |
| Oenotheraceae | Lythraceae | 2 |
| Boraginaceae | Namaceae | 2 |
| Fabaceae | Asteraceae | 2 |
| Boraginaceae | Heliotropiaceae | 1 |
| Actiniscaceae | Asteraceae | 1 |
| Cornnaraceae | Connaraceae | 1 |
| Polypodiaceae | Lindsaeaceae | 1 |
| Corallinaceae | Mesophyllumaceae | 1 |
| Nitrariaceae | Tetradiclidaceae | 1 |
| Rhodellaceae | Glaucosphaeraceae | 1 |
| Dothioraceae | Saccotheciaceae | 1 |
| Pseudoalteromonadaceae | Alteromonadaceae | 1 |
| Clavicipaceae | Cordycipitaceae | 1 |
| Sterculiaaaceae | Malvaceae | 1 |
| Buxaceae | Asphodelaceae | 1 |
| Fragilariaceae | Bacillariaceae | 1 |
| Oleaceae | Ustilaginaceae | 1 |
| Acoraceae | Rosaceae | 1 |
| Clusiaceae | Calophyllaceae | 1 |
| Myricaceae | Podocarpaceae | 1 |
| Cururbitaceae | Cucurbitaceae | 1 |
| Rubiaceae | Rutaceae | 1 |
| Iauraceae | Lauraceae | 1 |
| Skeletonemataceae | Skeletonemaceae | 1 |
| Rutaceae | Cistaceae | 1 |
| Fabaceae | Oleaceae | 1 |
| Thymelaeaceae | Parmeliaceae | 1 |
| Orobanchaceae | Rehmanniaceae | 1 |
| Amaranthaceae | Sapotaceae | 1 |
| Cystoseiraceae | Sargassaceae | 1 |
| Pleurochrysidaceae | Syracosphaeraceae | 1 |
| Lessoniaceae | Laminariaceae | 1 |
| Eutreptiaceae | Eutreptiidae | 1 |
| Grossuliriaceae | Grossulariaceae | 1 |
| Chlamydomonadaceae | Chlorodendraceae | 1 |
| Passifloraceae | Turneraceae | 1 |
| Apiaceae | Sparassidaceae | 1 |
| Asteraceae | Berberidaceae | 1 |
| Asteraceae | Amaryllidaceae | 1 |
| Agaveaceae | Asparagaceae | 1 |
| Convulvulaceae | Convolvulaceae | 1 |
| Poaceae | Arecaceae | 1 |
| Crombretaceae | Combretaceae | 1 |
| Loganiaceae | Streptococcaceae | 1 |
| Fagaceae | Moraceae | 1 |
| Phyllanthaceae | Funariaceae | 1 |
| Sacharomycetaceae | Saccharomycetaceae | 1 |
| Cyatheaceae | Cibotiaceae | 1 |
| Loganiaceae | Gentianaceae | 1 |
| Gelidiaceae | Gelidiellaceae | 1 |
| Glusiaceae | Clusiaceae | 1 |
| Polyporaceae | Albatrellaceae | 1 |
| Appiaceae | Apiaceae | 1 |
| Fabaceae | Streptococcaceae | 1 |
| Vinaceae | Vitaceae | 1 |
| Crassulaceae | Nelumbonaceae | 1 |
| Clusiaceae | Hypericaceae | 1 |
| Asteraceae | Fragilariaceae | 1 |
| Nymphaeaceae | Cabombaceae | 1 |
| Marasmiaceae | Omphalotaceae | 1 |
| Theaceae | Anacardiaceae | 1 |
| Miliaceae | Meliaceae | 1 |
| Cephalotaxaceae | Taxaceae | 1 |
| Sapindicaceae | Sapindaceae | 1 |
| Chlorellaceae | Oocystaceae | 1 |
| Phyllathaceae | Phyllanthaceae | 1 |
| Polypodiaceae | Hymenochaetaceae | 1 |
| Brassicaceae | Magnoliaceae | 1 |
| Schizotrichaceae | Trichocoleusaceae | 1 |
| Saururaceae | Enterococcaceae | 1 |
| Acoraceae | Moraceae | 1 |
| Brassicaceae | Oleiphilaceae | 1 |
| Gigartinaceae | Phyllophoraceae | 1 |
| Myrcinaceae | Primulaceae | 1 |
| Balanitaceae | Zygophyllaceae | 1 |
| Amarathaceae | Amaranthaceae | 1 |
| Mimosaceae | Fabaceae | 1 |
| Pycnococcaceae | Prasinococcaceae | 1 |
| Anacardiaceae | Simaroubaceae | 1 |
| Eustigmataceae | Monodopsidaceae | 1 |
| Zingeberaceae | Zingiberaceae | 1 |
| Araliaceae | Cordycipitaceae | 1 |
| Fagaceae | Fabaceae | 1 |
| Sapindaceae | Poaceae | 1 |
| Corylaceae | Betulaceae | 1 |
| Trapaceae | Lythraceae | 1 |
| Solenaceae | Solanaceae | 1 |
| Globularaceae | Plantaginaceae | 1 |
| Simaroubaceae | Irvingiaceae | 1 |
| Mimoaceae | Fabaceae | 1 |
| Boranginaceae | Boraginaceae | 1 |
| Malvaceae | Asteraceae | 1 |
| Cyantheaceae | Cyatheaceae | 1 |
| Balanophoraceae | Cynomoriaceae | 1 |
| Polypodiaceae | Onocleaceae | 1 |
| Moraceae | Salvadoraceae | 1 |
| Lythaceae | Lythraceae | 1 |
| Streliziaceae | Strelitziaceae | 1 |
| Merryliaceae | Meruliaceae | 1 |
| Cucurbitaceae | Arecaceae | 1 |
| Hypneaceae | Cystocloniaceae | 1 |
| Gelidiaceae | Plocamiaceae | 1 |
| Melanthiaceae | Nartheciaceae | 1 |
| Linnaeaceae | Caprifoliaceae | 1 |
| Laminariaceae | Costariaceae | 1 |
| Gephyrocapsaceae | Noelaerhabdaceae | 1 |
| Gomontiaceae | Monostromataceae | 1 |
| Mackinlayaceae | Apiaceae | 1 |
| Cantharellaceae | Hydnaceae | 1 |
| Apiaceae | Santalaceae | 1 |
| Oleraceae | Arecaceae | 1 |
| Chlorogloeopsidaceae | Nostocaceae | 1 |
| Asreraceae | Asteraceae | 1 |
| Aloaceae | Asphodelaceae | 1 |

## 三、生物界別分布

資料集名為「植物」萃取物，實際含藻類、真菌與地衣。統計時須分流，否則「植物」結論會被污染。

| kingdom | 列數 |
| --- | --- |
| Plantae | 7373 |
| (未定) | 128 |
| Fungi | 87 |
| Chromista | 78 |
| Bacteria | 23 |
| Protozoa | 1 |

## 四、需人工抽查者

| 類型 | 筆數 | 說明 |
| --- | --- | --- |
| FUZZY 且改變種小名 ⚠️ | 47 | 最高風險：既猜拼字又跟了同物異名 |
| FUZZY 比對（全部） | 54 | GBIF 靠模糊比對命中，拼字與原文不同 |
| 屬層級退回 | 116 | 種名查無，僅取到屬與科 |
| 完全查無 | 54 | 無科別，不進入圖譜 |

### FUZZY 且改變種小名的逐筆清單

| COSING 寫法 | GBIF 接受名 | 信心 |
| --- | --- | --- |
| Styrach obassis | Styrax obassia | 80 |
| Schizandra nigra | Schisandra repanda | 84 |
| Torulaspora delbruekii | Debaryomyces delbrueckii | 92 |
| Carapa guaianensis | Carapa guianensis | 93 |
| Lilium hybrid | Lilium hybr | 93 |
| Origanum cretium | Origanum creticum | 93 |
| Pinus tabulaeformis | Pinus tabuliformis | 93 |
| Sargassum pallidum | Sargassum polyporum | 93 |
| Terminalia bellerica | Terminalia bellirica | 93 |
| Tulipa hybrida | Tulipa hybr | 93 |
| Vetiveria zizanoides | Vetiveria zizanioides | 93 |
| Boswellia carterii | Boswellia sacra | 94 |
| Commiphora erythrea | Commiphora kataf | 94 |
| Polypodium leucotomos | Phlebodium aureum | 94 |
| Pomaderris kumerahou | Pomaderris kumarahou | 94 |
| Rosa kamchatica | Rosa rugosa | 94 |
| Rubus ellipiticus | Rubus ellipticus | 94 |
| Bifidobacterium is | Bifidobacterium | 95 |
| Bromelia balansea | Bromelia balansae | 95 |
| Carex humillis | Carex humilis | 95 |
| Cryptolepis buchanani | Cryptolepis buchananii | 95 |
| Dacrydium franklini | Lagarostrobos franklinii | 95 |
| Eriocaulon buergarianum | Eriocaulon buergerianum | 95 |
| Euterpe oleraceae | Euterpe oleracea | 95 |
| Pinus korainsis | Pinus koraiensis | 95 |
| Polystichum retrosopalaceum | Polystichum retrosopaleaceum | 95 |
| Thaumatococcus danielli | Thaumatococcus daniellii | 95 |
| Thymus serpillum | Thymus serpyllum | 95 |
| Acanthopanax koreanum | Eleutherococcus divaricatus | 96 |
| Camellia kissi | Camellia kissii | 96 |
| Canna hybrid | Canna hybrida | 96 |
| Citrus aurantifolia | Citrus aurantiifolia | 96 |
| Fritillaria ussuriensis | Fritillaria usuriensis | 96 |
| Ganoderma neo-japonicum | Ganoderma neojaponicum | 96 |
| Machilus odoratissima | Machilus odoratissimus | 96 |
| Magnolia liliflora | Magnolia liliiflora | 96 |
| Mentha haplocalix | Mentha canadensis | 96 |
| Myrothamnus flabellifolia | Myrothamnus flabellifolius | 96 |
| Narcissus pseudo-narcissus | Narcissus pseudonarcissus | 96 |
| Nuphar japonicum | Nuphar japonica | 96 |
| Nuphar luteum | Nuphar lutea | 96 |
| Pueraria thomsoni | Pueraria montana | 96 |
| Santalum spicata | Santalum spicatum | 96 |
| Schinopsis quebracho-colorado | Schinopsis quebrachocolorado | 96 |
| Schinus terebinthifolius | Schinus terebinthifolia | 96 |
| Taraxacum hallaisanensis | Taraxacum hallaisanense | 96 |
| Tetraselmis chui | Tetraselmis chuii | 96 |

## 五、驗收檢查

| 檢查項 | 結果 |
| --- | --- |
| 每個生物來源列都有科別 | ✅ 通過 |
| APG IV 拆分科全數判定完畢（0 筆待決） | ✅ 通過 |
| 物種解析率 > 90% | ✅ 通過 |
| 同物異名已統一到接受名 | ✅ 通過 |
| 科名不一致者全部留有紀錄 | ✅ 通過 |
| 無動物界誤配 | ✅ 通過 |
