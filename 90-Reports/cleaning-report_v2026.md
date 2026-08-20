# Phase 1 清理報告 — 2026 全庫

- 生物來源列：**7690**
- 科名寫法（原始）：**448** 種
- 科名寫法（正規化後）：**398** 種
- 經過科名修正的列：**1084**
- 待 GBIF 判定（APG IV 拆分科）：**136**

## 科名正規化的合併效果

| family_raw | family_accepted | 列數 | 修正類型 |
| --- | --- | --- | --- |
| Leguminosae | Fabaceae | 219 | nomenclature |
| Labiatae | Lamiaceae | 156 | nomenclature |
| Compositae | Asteraceae | 119 | nomenclature |
| Liliaceae | (待 GBIF) | 104 | needs_gbif |
| Umbelliferae | Apiaceae | 78 | nomenclature |
| Gramineae | Poaceae | 46 | nomenclature |
| Palmaceae | Arecaceae | 44 | typo |
| Chenopodiaceae | Amaranthaceae | 37 | nomenclature |
| Scrophulariaceae | (待 GBIF) | 31 | needs_gbif |
| Sterculiaceae | Malvaceae | 24 | nomenclature |
| Tiliaceae | Malvaceae | 23 | nomenclature |
| Agavaceae | Asparagaceae | 21 | nomenclature |
| Punicaceae | Lythraceae | 18 | nomenclature |
| Valerianaceae | Caprifoliaceae | 16 | nomenclature |
| Laminaceae | Lamiaceae | 13 | typo |
| Hippocastanaceae | Sapindaceae | 11 | nomenclature |
| Anacardaceae | Anacardiaceae | 10 | typo |
| Anonaceae | Annonaceae | 9 | typo |
| Simarubaceae | Simaroubaceae | 9 | typo |
| Aceraceae | Sapindaceae | 8 | nomenclature |
| Bombacaceae | Malvaceae | 7 | nomenclature |
| Taxodiaceae | Cupressaceae | 7 | nomenclature |
| Asclepiadaceae | Apocynaceae | 6 | nomenclature |
| Myrsinaceae | Primulaceae | 6 | nomenclature |
| Xanthorrhoeaceae | Asphodelaceae | 5 | nomenclature |
| Cruciferae | Brassicaceae | 5 | nomenclature |
| Illiciaceae | Schisandraceae | 5 | nomenclature |
| Fumariaceae | Papaveraceae | 5 | nomenclature |
| Guttiferae | Clusiaceae | 5 | nomenclature |
| Ruscaceae | Asparagaceae | 4 | nomenclature |
| Flacourtiaceae | Salicaceae | 3 | nomenclature |
| Elagnaceae | Elaeagnaceae | 3 | typo |
| Cypressaceae | Cupressaceae | 3 | typo |
| Palmae | Arecaceae | 3 | nomenclature |
| Capparidaceae | Capparaceae | 2 | nomenclature |
| Furaceae | Fucaceae | 2 | typo |
| Samydaceae | Salicaceae | 2 | nomenclature |
| Cannabidaceae | Cannabaceae | 2 | typo |
| Pyrolaceae | Ericaceae | 2 | nomenclature |
| Dipsacaceae | Caprifoliaceae | 1 | nomenclature |
| Hydrophyllaceae | Boraginaceae | 1 | nomenclature |
| Valeriabaceae | Caprifoliaceae | 1 | typo |
| Borraginaceae | Boraginaceae | 1 | typo |
| Cuscutaceae | Convolvulaceae | 1 | nomenclature |
| Myoporaceae | (待 GBIF) | 1 | needs_gbif |
| Zygopuhyllaceae | Zygophyllaceae | 1 | typo |
| Maranthaceae | Marantaceae | 1 | typo |
| Apieaceae | Apiaceae | 1 | typo |
| Julianiaceae | Anacardiaceae | 1 | nomenclature |
| Callophyllaceae | Calophyllaceae | 1 | typo |

## 解析狀態分布

| taxon_status | 列數 |
| --- | --- |
| agree | 7445 |
| inci_not_binomial | 80 |
| spelling_variant | 64 |
| resolved_by_gbif | 38 |
| excluded | 27 |
| genus_level_entry | 17 |
| inci_truncated | 12 |
| hyphen_split | 5 |
| desc_unparsed | 2 |

## 經 GBIF 查證後更正

INCI 與敘述的兩個名稱在 GBIF 骨幹中指向同一個接受名，屬同物異名，已更正為接受名。

| ref_no | 更正為 |
| --- | --- |
| 32489 | Centaurium erythraea |
| 33009 | Avena sativa |
| 39318 | Cinnamomum camphora |
| 54453 | Ananas comosus |
| 57821 | Macrocystis pyrifera |
| 58009 | Punica granatum |
| 59538 | Saccharina latissima |
| 59972 | Prunus amygdalus |
| 76054 | Syzygium aromaticum |
| 79762 | Rosa moschata |
| 84041 | Dendropanax morbiferus |
| 84042 | Dendropanax morbiferus |
| 84757 | Ganoderma lucidum |
| 87118 | Lathyrus oleraceus |
| 87170 | Adenium obesum |
| 87247 | Camellia sinensis |
| 87287 | Citrus aurantium |
| 88634 | Opuntia ficus-indica |
| 89276 | Rosa davurica |
| 91489 | Allium hookeri |
| 91540 | Oryza sativa |
| 91985 | Oryza sativa |
| 92537 | Citrus aurantium |
| 92579 | Pelargonium graveolens |
| 92612 | Firmiana simplex |
| 92748 | Juglans regia |
| 93433 | Stemona sessilifolia |
| 94308 | Cistus creticus |
| 94343 | Laurus nobilis |
| 95313 | Passiflora cincinnata |
| 95361 | Dendropanax morbiferus |
| 95474 | Houttuynia cordata |
| 95475 | Centella asiatica |
| 95781 | Oryza sativa |
| 95869 | Sophora flavescens |
| 96062 | Citrus reticulata |
| 96092 | Boswellia sacra |
| 96151 | Helianthus annuus |

## 查無定論，未納入圖譜

INCI 名稱與敘述指向**兩個不同的接受種**，GBIF 無法判斷原意為何。這些成分仍留在 `ingredient` 主表，但不建立物種／屬／科連結，因此不會污染分類階層。

| ref_no | INCI 名稱 |
| --- | --- |
| 33447 | DIMETHICONOL ILLIPE BUTTERATE |
| 34178 | GUTTA PERCHA |
| 39380 | COPAIFERA RETICULATA BALSAM OIL ACETYLATED |
| 54790 | BACCHARIS TRIMERA EXTRACT |
| 56449 | HIBISCUS ROSA-SINENSIS FLOWER POWDER |
| 59357 | ROSA RUGOSA BUD POWDER |
| 59358 | ROSA RUGOSA FLOWER EXTRACT |
| 59359 | ROSA RUGOSA LEAF EXTRACT |
| 82823 | HIBISCUS ROSA-SINENSIS FLOWER EXTRACT |
| 83098 | HIBISCUS ROSA-SINENSIS LEAF EXTRACT |
| 83588 | ROSA RUGOSA FLOWER OIL |
| 86471 | ELAEIS OLEIFERA KERNEL OIL |
| 87246 | ASPERGILLUS/BUCKWHEAT FERMENT EXTRACT |
| 89409 | ASPERGILLUS/LACTOBACILLUS/CAMELLIA SINENSIS LEAF FERMENT EXTRACT |
| 89657 | APHANOTHECE SACRUM POWDER |
| 89992 | VACCINIUM CORYMBOSUM SEED |
| 90906 | PANAX GINSENG CALLUS CULTURE CONDITIONED MEDIA |
| 92884 | PYROCYSTIS NOCTILUCA LYSATE |
| 93735 | ADIANTUM CAPILLUS-VENERIS LEAF EXTRACT |
| 94323 | ROSA FLORIBUNDA CALLUS EXTRACT |
| 94794 | CRYPTOCOCCUS/HUMUS FERMENT FILTRATE |
| 94974 | GALACTOMYCES/SOYMILK FERMENT FILTRATE |
| 95033 | LACTOBACILLUS/LEUCONOSTOC/POLYSORBATE 80/PORTULACA OLERACEA EXTRACT FERMENT LYSATE FILTRATE |
| 95034 | LACTOBACILLUS/LEUCONOSTOC/ARTEMISIA ANNUA EXTRACT/POLYSORBATE 80 FERMENT LYSATE FILTRATE |
| 97037 | RHIZOPUS/BORAGO OFFICINALIS SEED OIL FERMENT FILTRATE |
| 97231 | SANTALUM PANICULATUM WOOD WATER |
| 97344 | AQUILARIA AGALLOCHA WOOD POWDER |

## 驗收檢查

| 檢查項 | 結果 |
| --- | --- |
| ingredient_v2026 有資料 | ✅ 通過 |
| Palmae/Palmaceae/Arecaceae 合併為單一科 | ✅ 通過 |
| Laminaceae -> Lamiaceae | ✅ 通過 |
| 屬名解析率 > 98% | ✅ 通過 |
| Liliaceae / Scrophulariaceae 未被科層級硬映射 | ✅ 通過 |
| 查無定論者未帶入物種連結 | ✅ 通過 |
| conflicts.csv 無未裁決項目 | ✅ 通過 |
