# Phase 4 — LOTUS 化學成分富集 (2026)

LOTUS 凍結版 2026-04-13：**674,454** 組「結構—生物—文獻」三元組，涵蓋 **37,469** 個生物、**227,319** 個化合物（InChIKey）。

以 Phase 2 產出的 **GBIF 接受名** join，非原始 COSING 名稱——LOTUS 使用接受名，用同物異名比對會漏掉大部分。

## 一、覆蓋率

| 項目 | 值 |
| --- | --- |
| 本專案物種數 | 2,827 |
| LOTUS 中查得到者 | **2,219**（78.5%）|
| 物種—化合物配對 | 126,775 |
| 有成分資料的萃取物 | 6,167 / 7,690（80.2%）|
| 種層級查無、但同屬有資料 | 494 |

## 二、⚠️ 覆蓋率偏誤（務必理解）

**LOTUS 查不到 ≠ 該物種沒有成分。** 只代表沒有已發表的植化研究。被研究得多的植物（藥用、經濟作物）覆蓋率高，冷門物種接近零。

本專案有 **608** 個物種在 LOTUS 中無資料。這些必須標記為「無資料」，**不可**與「無成分」混為一談——否則所有下游分析都會系統性偏向熱門植物。

## 三、成分最多的物種

| 物種 | 化合物數 |
| --- | --- |
| Arabidopsis thaliana | 1,016 |
| Nicotiana tabacum | 860 |
| Solanum lycopersicum | 808 |
| Mangifera indica | 771 |
| Tripterygium wilfordii | 747 |
| Camellia sinensis | 715 |
| Zingiber officinale | 713 |
| Ganoderma lucidum | 696 |
| Phaseolus vulgaris | 663 |
| Panax ginseng | 653 |
| Capsicum annuum | 650 |
| Citrus reticulata | 574 |

## 四、各科的 LOTUS 覆蓋率

覆蓋率高低反映的是**研究熱度**，不是化學豐富度。

| 科 | 物種數 | 有成分資料 | 覆蓋率 |
| --- | --- | --- | --- |
| Papaveraceae | 20 | 20 | 100% |
| Pinaceae | 51 | 50 | 98% |
| Sapindaceae | 22 | 21 | 95% |
| Araliaceae | 20 | 19 | 95% |
| Oleaceae | 20 | 19 | 95% |
| Cupressaceae | 27 | 25 | 93% |
| Rubiaceae | 29 | 26 | 90% |
| Apocynaceae | 28 | 25 | 89% |
| Apiaceae | 65 | 57 | 88% |
| Cucurbitaceae | 24 | 21 | 88% |
| Asteraceae | 195 | 170 | 87% |
| Brassicaceae | 31 | 27 | 87% |
| Amaryllidaceae | 23 | 20 | 87% |
| Plantaginaceae | 21 | 18 | 86% |

## 五、驗收檢查

| 檢查項 | 結果 |
| --- | --- |
| lotus_pair 已載入 | ✅ 通過 |
| 以 GBIF 接受名 join | ✅ 通過 |
| 物種覆蓋率 > 20% | ✅ 通過 |
| 「無資料」與「無成分」分開統計 | ✅ 通過 |
