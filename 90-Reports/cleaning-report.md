# Phase 1 清理報告

- 生物來源列：**3862**
- 科名寫法（原始）：**236** 種
- 科名寫法（正規化後）：**189** 種
- 經過科名修正的列：**836**
- 待 GBIF 判定（APG IV 拆分科）：**67**

## 科名正規化的合併效果

| family_raw | family_accepted | 列數 | 修正類型 |
| --- | --- | --- | --- |
| Leguminosae | Fabaceae | 162 | nomenclature |
| Labiatae | Lamiaceae | 153 | nomenclature |
| Compositae | Asteraceae | 110 | nomenclature |
| Umbelliferae | Apiaceae | 73 | nomenclature |
| Liliaceae | (待 GBIF) | 53 | needs_gbif |
| Gramineae | Poaceae | 43 | nomenclature |
| Palmaceae | Arecaceae | 35 | typo |
| Tiliaceae | Malvaceae | 20 | nomenclature |
| Sterculiaceae | Malvaceae | 19 | nomenclature |
| Agavaceae | Asparagaceae | 16 | nomenclature |
| Chenopodiaceae | Amaranthaceae | 15 | nomenclature |
| Punicaceae | Lythraceae | 15 | nomenclature |
| Scrophulariaceae | (待 GBIF) | 13 | needs_gbif |
| Valerianaceae | Caprifoliaceae | 13 | nomenclature |
| Hippocastanaceae | Sapindaceae | 8 | nomenclature |
| Simarubaceae | Simaroubaceae | 8 | typo |
| Anonaceae | Annonaceae | 7 | typo |
| Bombacaceae | Malvaceae | 6 | nomenclature |
| Guttiferae | Clusiaceae | 6 | nomenclature |
| Asclepiadaceae | Apocynaceae | 5 | nomenclature |
| Taxodiaceae | Cupressaceae | 5 | nomenclature |
| Illiciaceae | Schisandraceae | 4 | nomenclature |
| Fumariaceae | Papaveraceae | 3 | nomenclature |
| Furaceae | Fucaceae | 3 | typo |
| Anacardaceae | Anacardiaceae | 3 | typo |
| Cypressaceae | Cupressaceae | 3 | typo |
| Palmae | Arecaceae | 3 | nomenclature |
| Myrsinaceae | Primulaceae | 3 | nomenclature |
| Elagnaceae | Elaeagnaceae | 3 | typo |
| Capparidaceae | Capparaceae | 2 | nomenclature |
| Ruscaceae | Asparagaceae | 2 | nomenclature |
| Cruciferae | Brassicaceae | 2 | nomenclature |
| Cannabidaceae | Cannabaceae | 2 | typo |
| Samydaceae | Salicaceae | 2 | nomenclature |
| Maranthaceae | Marantaceae | 1 | typo |
| Cuscutaceae | Convolvulaceae | 1 | nomenclature |
| Flacourtiaceae | Salicaceae | 1 | nomenclature |
| Callophyllaceae | Calophyllaceae | 1 | typo |
| Myoporaceae | (待 GBIF) | 1 | needs_gbif |
| Julianiaceae | Anacardiaceae | 1 | nomenclature |
| Pyrolaceae | Ericaceae | 1 | nomenclature |
| Hydrophyllaceae | Boraginaceae | 1 | nomenclature |
| Aceraceae | Sapindaceae | 1 | nomenclature |
| Zygopuhyllaceae | Zygophyllaceae | 1 | typo |
| Laminaceae | Lamiaceae | 1 | typo |
| Valeriabaceae | Caprifoliaceae | 1 | typo |
| Borraginaceae | Boraginaceae | 1 | typo |
| Xanthorrhoeaceae | Asphodelaceae | 1 | nomenclature |
| Apieaceae | Apiaceae | 1 | typo |
| Dipsacaceae | Caprifoliaceae | 1 | nomenclature |

## 解析狀態分布

| taxon_status | 列數 |
| --- | --- |
| agree | 3789 |
| inci_not_binomial | 32 |
| genus_level_entry | 17 |
| excluded | 8 |
| hyphen_split | 6 |
| resolved_by_gbif | 4 |
| inci_truncated | 4 |
| desc_unparsed | 1 |
| spelling_variant | 1 |

## 經 GBIF 查證後更正

INCI 與敘述的兩個名稱在 GBIF 骨幹中指向同一個接受名，屬同物異名，已更正為接受名。

| ref_no | 更正為 |
| --- | --- |
| 32489 | Centaurium erythraea |
| 39318 | Cinnamomum camphora |
| 76054 | Syzygium aromaticum |
| 96092 | Boswellia sacra |

## 查無定論，未納入圖譜

INCI 名稱與敘述指向**兩個不同的接受種**，GBIF 無法判斷原意為何。這些成分仍留在 `ingredient` 主表，但不建立物種／屬／科連結，因此不會污染分類階層。

| ref_no | INCI 名稱 |
| --- | --- |
| 34178 | GUTTA PERCHA |
| 39380 | COPAIFERA RETICULATA BALSAM OIL ACETYLATED |
| 59357 | ROSA RUGOSA BUD POWDER |
| 59358 | ROSA RUGOSA FLOWER EXTRACT |
| 59359 | ROSA RUGOSA LEAF EXTRACT |
| 83588 | ROSA RUGOSA FLOWER OIL |
| 86471 | ELAEIS OLEIFERA KERNEL OIL |
| 94152 | OENOCARPUS BATAUA ACID |

## 驗收檢查

| 檢查項 | 結果 |
| --- | --- |
| ingredient 總列數 = 13,622 | ✅ 通過 |
| Palmae/Palmaceae/Arecaceae 合併為單一科 | ✅ 通過 |
| Laminaceae -> Lamiaceae | ✅ 通過 |
| 屬名解析率 > 98% | ✅ 通過 |
| Liliaceae / Scrophulariaceae 未被科層級硬映射 | ✅ 通過 |
| 查無定論者未帶入物種連結 | ✅ 通過 |
| conflicts.csv 無未裁決項目 | ✅ 通過 |
