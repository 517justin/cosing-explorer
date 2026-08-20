# Phase 3 — 使用部位與製程抽取報告

全部以詞表比對完成，未使用 LLM。詞表位於 `_data/vocab/`。

- 有使用部位：**3504 / 3862**（90.7%）
  - 由 INCI 名稱取得：3091
  - 由製程反推（如 seedcake→seed）：9
  - 由敘述補回：404
- 有製程：**3630**（94.0%）
- 有製程修飾語：**69**
- 細胞培養來源：**112**
- 部位未標示（留空，不臆測）：**358**

## 一、使用部位分布

| 部位 | 列數 |
| --- | --- |
| leaf | 853 |
| flower | 570 |
| seed | 524 |
| fruit | 467 |
| root | 351 |
| stem | 314 |
| whole_plant | 208 |
| aerial_part | 175 |
| bark | 137 |
| wood | 98 |
| peel | 77 |
| gum | 44 |
| resin | 43 |
| bud | 42 |
| rhizome | 33 |
| sprout | 16 |
| balsam | 14 |
| bulb | 9 |
| thallus | 8 |
| cone | 5 |
| sap | 5 |
| lees | 2 |
| cob | 2 |
| tuber | 2 |
| cap | 1 |
| gall | 1 |
| sclerotium | 1 |

## 二、製程分布

| 製程 | 列數 |
| --- | --- |
| extract | 2199 |
| oil | 663 |
| powder | 260 |
| water | 231 |
| juice | 115 |
| wax | 59 |
| butter | 21 |
| protein | 15 |
| flour | 14 |
| seedcake | 9 |
| starch | 8 |
| meal | 6 |
| acid | 4 |
| lipids | 4 |
| polysaccharide | 4 |
| sterols | 3 |
| tar | 3 |
| fiber | 3 |
| unsaponifiables | 2 |
| absolute | 2 |
| ash | 1 |
| malt | 1 |
| tincture | 1 |
| catechins | 1 |
| nonvolatiles | 1 |

## 三、製程修飾語

| 修飾語 | 列數 |
| --- | --- |
| hydrolyzed | 23 |
| acetylated | 14 |
| expressed | 13 |
| hydrogenated | 5 |
| rectified | 3 |
| oxidized | 3 |
| epoxidized | 2 |
| distilled | 1 |
| sulfurized | 1 |
| acetylated+sulfated | 1 |
| steam_distilled | 1 |
| acetylated+hydrogenated | 1 |
| saponified | 1 |
| modified | 1 |

## 四、科 × 部位的集中處

同一科的萃取物集中使用哪個部位，是 Phase 5 關聯分析的輸入之一。

| 科 | 部位 | 列數 |
| --- | --- | --- |
| Lamiaceae | leaf | 75 |
| Asteraceae | flower | 68 |
| Lamiaceae | aerial_part | 68 |
| Rosaceae | fruit | 63 |
| Rutaceae | peel | 60 |
| Rosaceae | flower | 56 |
| Rosaceae | seed | 49 |
| Poaceae | seed | 49 |
| Fabaceae | seed | 47 |
| Rutaceae | fruit | 45 |
| Lamiaceae | flower, leaf, stem | 44 |
| Myrtaceae | leaf | 43 |

## 五、可橫向比較的物種

同一物種被以四種以上不同部位收錄者。同物種不同部位的成分譜可能天差地遠，這些是最適合做橫向比較的群組。

| 物種 | 部位種類數 | 萃取物數 |
| --- | --- | --- |
| Vitis vinifera | 10 | 21 |
| Cupressus sempervirens | 8 | 11 |
| Citrus aurantium | 7 | 54 |
| Nelumbo nucifera | 7 | 22 |
| Olea europaea | 7 | 20 |
| Prunus persica | 7 | 14 |
| Punica granatum | 7 | 13 |
| Prunus cerasus | 7 | 11 |
| Cinnamomum camphora | 6 | 19 |
| Prunus amygdalus | 6 | 18 |
| Camellia sinensis | 6 | 14 |
| Panax ginseng | 6 | 14 |

## 六、驗收檢查

| 檢查項 | 結果 |
| --- | --- |
| 部位涵蓋率 > 75% | ✅ 通過 |
| 製程涵蓋率 > 90% | ✅ 通過 |
| 複合部位已拆成多值 | ✅ 通過 |
| 未標示部位者留空，未臆測為全株 | ✅ 通過 |
