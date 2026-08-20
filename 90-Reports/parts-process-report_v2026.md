# Phase 3 — 使用部位與製程抽取報告

全部以詞表比對完成，未使用 LLM。詞表位於 `_data/vocab/`。

- 有使用部位：**6655 / 7690**（86.5%）
  - 由 INCI 名稱取得：5686
  - 由製程反推（如 seedcake→seed）：32
  - 由敘述補回：937
- 有製程：**7203**（93.7%）
- 有製程修飾語：**140**
- 細胞培養來源：**507**
- 部位未標示（留空，不臆測）：**1035**

## 一、使用部位分布

| 部位 | 列數 |
| --- | --- |
| leaf | 1663 |
| flower | 987 |
| seed | 919 |
| fruit | 852 |
| whole_plant | 705 |
| stem | 703 |
| root | 674 |
| bark | 275 |
| aerial_part | 192 |
| wood | 154 |
| peel | 134 |
| bud | 66 |
| rhizome | 63 |
| resin | 58 |
| sprout | 55 |
| gum | 50 |
| bulb | 24 |
| sap | 23 |
| balsam | 14 |
| thallus | 12 |
| tuber | 9 |
| cone | 8 |
| lees | 4 |
| gall | 3 |
| cob | 2 |
| sclerotium | 2 |
| cap | 1 |

## 二、製程分布

| 製程 | 列數 |
| --- | --- |
| extract | 4915 |
| oil | 973 |
| powder | 460 |
| water | 387 |
| juice | 201 |
| wax | 97 |
| butter | 41 |
| seedcake | 32 |
| protein | 19 |
| flour | 13 |
| starch | 10 |
| polysaccharide | 10 |
| fiber | 9 |
| meal | 7 |
| sterols | 6 |
| lipids | 5 |
| acid | 5 |
| tar | 3 |
| absolute | 2 |
| catechins | 2 |
| unsaponifiables | 2 |
| nonvolatiles | 1 |
| tincture | 1 |
| ash | 1 |
| malt | 1 |

## 三、製程修飾語

| 修飾語 | 列數 |
| --- | --- |
| hydrolyzed | 87 |
| acetylated | 14 |
| expressed | 14 |
| hydrogenated | 9 |
| oxidized | 4 |
| rectified | 3 |
| epoxidized | 2 |
| sulfurized | 1 |
| distilled | 1 |
| modified | 1 |
| sulfated | 1 |
| acetylated+sulfated | 1 |
| steam_distilled | 1 |
| acetylated+hydrogenated | 1 |
| saponified | 1 |

## 四、科 × 部位的集中處

同一科的萃取物集中使用哪個部位，是 Phase 5 關聯分析的輸入之一。

| 科 | 部位 | 列數 |
| --- | --- | --- |
| Rosaceae | fruit | 111 |
| Rutaceae | peel | 103 |
| Fabaceae | seed | 101 |
| Asteraceae | flower | 98 |
| Rutaceae | fruit | 98 |
| Lamiaceae | leaf | 96 |
| Rosaceae | flower | 87 |
| Asteraceae | whole_plant | 78 |
| Rosaceae | seed | 76 |
| Poaceae | seed | 69 |
| Lamiaceae | aerial_part | 68 |
| Lamiaceae | flower, leaf, stem | 62 |

## 五、可橫向比較的物種

同一物種被以四種以上不同部位收錄者。同物種不同部位的成分譜可能天差地遠，這些是最適合做橫向比較的群組。

| 物種 | 部位種類數 | 萃取物數 |
| --- | --- | --- |
| Vitis vinifera | 11 | 27 |
| Panax ginseng | 10 | 24 |
| Prunus mume | 9 | 16 |
| Citrus aurantium | 8 | 84 |
| Olea europaea | 8 | 23 |
| Camellia sinensis | 8 | 21 |
| Punica granatum | 8 | 16 |
| Phyllostachys edulis | 8 | 12 |
| Morus alba | 8 | 11 |
| Cupressus sempervirens | 8 | 10 |
| Cinnamomum camphora | 7 | 25 |
| Citrus limon | 7 | 25 |

## 六、驗收檢查

| 檢查項 | 結果 |
| --- | --- |
| 部位涵蓋率 > 75% | ✅ 通過 |
| 製程涵蓋率 > 90% | ✅ 通過 |
| 複合部位已拆成多值 | ✅ 通過 |
| 未標示部位者留空，未臆測為全株 | ✅ 通過 |
