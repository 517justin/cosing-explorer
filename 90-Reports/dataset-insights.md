# COSING 資料集分析 — Phase 0–3 的認識

由 `_scripts/07_insights.py` 於 2026-08-20 自 `_data/kb.duckdb` 產生。
所有數字為即時查詢，每節附上產生它的 SQL。

> 本報告只陳述**資料本身支持的結論**。需要外部知識才能解讀的地方，一律標明。

---

## 摘要

1. 這不是植物資料庫——**71.6%** 是合成化學品，生物來源僅 **28.4%**
2. 植物與合成品在用途上分工明確：植物做訴求型功效，合成做物理型功能
3. 科與使用部位有強對應，化學分類學的前提成立
4. 法規限制高度集中於特定科，但條文內容不在本資料集內
5. 長尾極重：40% 的物種只出現一次
6. 這是一份 **2019-11-21 的快照**，距今約 6 年未更新
7. `SKIN CONDITIONING` 標籤涵蓋 59% 的生物來源，幾乎沒有區辨力

---

## 一、資料集的組成

### 這不是植物資料庫

專案名為「植物萃取物知識圖譜」，但資料主體不是植物。圖譜的分類階層只建在生物來源子集上，其餘留在主表供查詢與比較。

| 類別 | 筆數 | 佔比 % |
| --- | --- | --- |
| 合成／非生物來源 | 9760 | 71.6 |
| 生物來源萃取物 | 3862 | 28.4 |

<details><summary>查詢語句</summary>

```sql
SELECT CASE WHEN e.ref_no IS NULL THEN '合成／非生物來源' ELSE '生物來源萃取物' END AS 類別,
       count(*) AS 筆數,
       round(count(*) * 100.0 / sum(count(*)) OVER (), 1) AS 佔比
FROM ingredient i LEFT JOIN extract e USING(ref_no)
GROUP BY 1 ORDER BY 2 DESC
```
</details>

### 生物來源中還混有藻類、真菌與地衣

統計時必須分流，否則「植物」的結論會被非植物污染。

| 界 | 筆數 |
| --- | --- |
| Plantae | 3782 |
| (GBIF 未定) | 36 |
| Chromista | 23 |
| Fungi | 21 |

<details><summary>查詢語句</summary>

```sql
SELECT coalesce(kingdom, '(GBIF 未定)') AS 界, count(*) AS 筆數
FROM extract GROUP BY 1 ORDER BY 2 DESC
```
</details>

---

## 二、植物與合成品的分工

### 植物負責訴求型功效，合成負責物理型功能

把同一個 `Function` 的兩種來源攤開比較。差異極大：滋補、收斂、舒緩幾乎只用植物；增稠、成膜、清潔幾乎全是合成品。

這不是化學決定的，是產業慣例與法規宣稱方式決定的——難以量化的訴求傾向用植物表述，可量測的物理功能用合成品達成。

| 用途 | 生物來源 | 合成 | 生物佔比 % |
| --- | --- | --- | --- |
| TONIC | 260 | 25 | 91.2 |
| ASTRINGENT | 218 | 75 | 74.4 |
| SOOTHING | 85 | 30 | 73.9 |
| MASKING | 625 | 363 | 63.3 |
| ABRASIVE | 132 | 78 | 62.9 |
| SKIN PROTECTING | 248 | 267 | 48.2 |
| SKIN CONDITIONING | 2276 | 2465 | 48.0 |
| ANTIOXIDANT | 216 | 363 | 37.3 |
| HUMECTANT | 146 | 336 | 30.3 |
| PERFUMING | 709 | 1945 | 26.7 |
| BULKING | 32 | 104 | 23.5 |
| ANTIMICROBIAL | 76 | 248 | 23.5 |
| EMOLLIENT | 282 | 1058 | 21.0 |
| ORAL CARE | 23 | 103 | 18.3 |
| HAIR CONDITIONING | 194 | 1002 | 16.2 |
| DEODORANT | 16 | 101 | 13.7 |
| BINDING | 30 | 246 | 10.9 |
| VISCOSITY CONTROLLING | 57 | 719 | 7.3 |
| FILM FORMING | 35 | 461 | 7.1 |
| EMULSION STABILISING | 14 | 239 | 5.5 |
| CLEANSING | 33 | 715 | 4.4 |
| NOT REPORTED | 6 | 149 | 3.9 |
| CHELATING | 3 | 123 | 2.4 |
| OPACIFYING | 3 | 138 | 2.1 |
| BUFFERING | 3 | 174 | 1.7 |
| HAIR DYEING | 3 | 209 | 1.4 |
| FOAMING | 2 | 148 | 1.3 |
| PLASTICISER | 1 | 109 | 0.9 |
| PRESERVATIVE | 1 | 163 | 0.6 |
| SURFACTANT | 8 | 1570 | 0.5 |
| COSMETIC COLORANT | 1 | 194 | 0.5 |
| EMULSIFYING | 7 | 1395 | 0.5 |
| FOAM BOOSTING | 1 | 230 | 0.4 |
| ANTISTATIC | 3 | 677 | 0.4 |
| SOLVENT | 1 | 406 | 0.2 |
| HYDROTROPE | 0 | 118 | 0.0 |

<details><summary>查詢語句</summary>

```sql
WITH bio AS (SELECT unnest(i.functions) f FROM ingredient i JOIN extract e USING(ref_no)),
     syn AS (SELECT unnest(i.functions) f FROM ingredient i
             LEFT JOIN extract e USING(ref_no) WHERE e.ref_no IS NULL),
     bc AS (SELECT f, count(*) c FROM bio GROUP BY 1),
     sc AS (SELECT f, count(*) c FROM syn GROUP BY 1)
SELECT coalesce(bc.f, sc.f) AS 用途,
       coalesce(bc.c, 0) AS 生物來源,
       coalesce(sc.c, 0) AS 合成,
       round(coalesce(bc.c,0) * 100.0 / (coalesce(bc.c,0) + coalesce(sc.c,0)), 1) AS 生物佔比
FROM bc FULL JOIN sc ON bc.f = sc.f
WHERE coalesce(bc.c,0) + coalesce(sc.c,0) >= 100
ORDER BY 4 DESC
```
</details>

---

## 三、科與使用部位的對應

### 各科集中使用特定部位，與次級代謝物的儲存位置相符

唇形科與桃金孃科取葉（精油腺在葉）、芸香科取果皮（油胞在外果皮）、禾本科取種子、柏科取木材。

**這是 Phase 5 圖譜有東西可挖的實證**——「親緣相近的植物產生相似次級代謝物」這個前提，在本資料上站得住。

| 科 | 部位標記數 | 最集中部位 | 筆數 | 佔該科 % |
| --- | --- | --- | --- | --- |
| Lamiaceae | 390 | leaf | 133 | 34.0 |
| Asteraceae | 305 | flower | 99 | 32.0 |
| Rosaceae | 256 | fruit | 66 | 26.0 |
| Fabaceae | 247 | seed | 50 | 20.0 |
| Rutaceae | 197 | peel | 61 | 31.0 |
| Apiaceae | 140 | seed | 28 | 20.0 |
| Pinaceae | 132 | leaf | 53 | 40.0 |
| Poaceae | 131 | seed | 50 | 38.0 |
| Myrtaceae | 102 | leaf | 57 | 56.0 |
| Malvaceae | 98 | flower | 27 | 28.0 |
| Cupressaceae | 87 | wood | 28 | 32.0 |
| Lauraceae | 67 | leaf | 22 | 33.0 |

<details><summary>查詢語句</summary>

```sql
WITH fp AS (
        SELECT family_final AS f, unnest(plant_part) AS p FROM extract
        WHERE plant_part IS NOT NULL AND family_final IS NOT NULL),
     t AS (SELECT f, count(*) AS tot FROM fp GROUP BY 1 HAVING tot >= 60)
SELECT fp.f AS 科, t.tot AS 部位標記數, fp.p AS 最集中部位,
       count(*) AS 該部位筆數, round(count(*) * 100.0 / t.tot, 0) AS 佔該科
FROM fp JOIN t USING(f) GROUP BY 1, 2, 3
QUALIFY row_number() OVER (PARTITION BY fp.f ORDER BY count(*) DESC) = 1
ORDER BY t.tot DESC
```
</details>

### 同一物種被以多個部位收錄者，是最適合橫向比較的群組

同物種不同部位的成分譜可能天差地遠，這些群組可直接做對照。

| 物種 | 萃取物數 | 部位組合數 | 製程數 |
| --- | --- | --- | --- |
| Vitis vinifera | 21 | 10 | 5 |
| Citrus aurantium | 54 | 7 | 6 |
| Nelumbo nucifera | 22 | 7 | 6 |
| Olea europaea | 20 | 7 | 6 |
| Cinnamomum camphora | 19 | 6 | 2 |
| Prunus amygdalus | 18 | 6 | 5 |
| Citrus limon | 20 | 5 | 5 |
| Oryza sativa | 20 | 5 | 7 |
| Lavandula angustifolia | 16 | 5 | 6 |
| Mentha piperita | 15 | 5 | 4 |
| Foeniculum vulgare | 16 | 4 | 3 |

<details><summary>查詢語句</summary>

```sql
SELECT species_accepted AS 物種, count(*) AS 萃取物數,
       count(DISTINCT list_sort(plant_part)) AS 部位組合數,
       count(DISTINCT process) AS 製程數
FROM extract WHERE species_accepted IS NOT NULL AND plant_part IS NOT NULL
GROUP BY 1 HAVING count(*) >= 15 ORDER BY 3 DESC, 2 DESC LIMIT 12
```
</details>

---

## 四、法規限制

### 生物來源整體受限率低於合成品

| 類別 | 總數 | 受限數 | 受限率 % |
| --- | --- | --- | --- |
| 合成 | 9760 | 914 | 9.4 |
| 生物來源 | 3862 | 159 | 4.1 |

<details><summary>查詢語句</summary>

```sql
SELECT CASE WHEN e.ref_no IS NULL THEN '合成' ELSE '生物來源' END AS 類別,
       count(*) AS 總數,
       count(*) FILTER (WHERE i.restriction IS NOT NULL) AS 受限數,
       round(count(*) FILTER (WHERE i.restriction IS NOT NULL) * 100.0 / count(*), 1) AS 受限率
FROM ingredient i LEFT JOIN extract e USING(ref_no) GROUP BY 1 ORDER BY 4 DESC
```
</details>

### 但拆到科層級，差異極大

| 科 | 受限數 | 該科總數 | 受限率 % |
| --- | --- | --- | --- |
| Rutaceae | 59 | 192 | 30.7 |
| Pinaceae | 57 | 109 | 52.3 |
| Cupressaceae | 10 | 80 | 12.5 |
| Lauraceae | 9 | 66 | 13.6 |
| Apiaceae | 7 | 141 | 5.0 |
| Fabaceae | 5 | 247 | 2.0 |
| Parmeliaceae | 4 | 6 | 66.7 |
| Altingiaceae | 4 | 4 | 100.0 |

<details><summary>查詢語句</summary>

```sql
SELECT e.family_final AS 科,
       count(*) FILTER (WHERE i.restriction IS NOT NULL) AS 受限數,
       count(*) AS 該科總數,
       round(count(*) FILTER (WHERE i.restriction IS NOT NULL) * 100.0 / count(*), 1) AS 受限率
FROM extract e JOIN ingredient i USING(ref_no)
WHERE e.family_final IS NOT NULL
GROUP BY 1 HAVING 受限數 >= 3 ORDER BY 2 DESC
```
</details>

### 受限品高度集中於少數條文，且每條只針對單一科

法規不是零散撒開的，是針對特定類群的特徵化學下的。

| 法規條文 | 筆數 | 橫跨科數 | 涉及的科 |
| --- | --- | --- | --- |
| II/358 R1 | 37 | 1 | Rutaceae |
| II/358 | 21 | 1 | Rutaceae |
| III/123 | 10 | 1 | Cupressaceae |
| III/110 | 9 | 1 | Pinaceae |
| III/103 | 6 | 1 | Pinaceae |
| III/122 | 6 | 1 | Pinaceae |
| II/360 R3 | 6 | 1 | Lauraceae |
| III/115 | 5 | 1 | Pinaceae |
| III/107 | 4 | 1 | Pinaceae |
| III/112 | 4 | 1 | Pinaceae |

<details><summary>查詢語句</summary>

```sql
SELECT i.restriction AS 法規條文, count(*) AS 筆數,
       count(DISTINCT e.family_final) AS 橫跨科數,
       string_agg(DISTINCT e.family_final, ', ') AS 涉及的科
FROM extract e JOIN ingredient i USING(ref_no)
WHERE i.restriction IS NOT NULL
GROUP BY 1 ORDER BY 2 DESC LIMIT 10
```
</details>

> ⚠️ **本資料集的限制**：`Restriction` 欄只有代碼（如 `II/358`），**不含法規全文**，個別條文禁的是什麼、限量多少，`COSING_CAS.csv` 答不出來。

> ✅ **已補上**：`_data/cosing_2026/` 收錄現行 Annex II–VI 條文（由 `_scripts/08_fetch_annexes.py` 自 CosIng 官方 API 擷取）。以代碼中的數字對應 Annex 的 `refNo` 即可查得條文。

> 例：`II/358` = **呋喃香豆素（furocoumarines）**——柑橘皮油中的光敏性成分。這正好解釋了為何受限的 61 筆集中在 Rutaceae（58）與 Apiaceae（2）：呋喃香豆素本來就是這兩個科的特徵代謝物。**這是化學分類學訊號，不是巧合。**

---

## 五、收錄的深度與長尾

### 四成物種只出現一次

| 出現次數 | 物種數 | 佔比 % |
| --- | --- | --- |
| 1 次 | 455 | 39.6 |
| 2 次 | 243 | 21.1 |
| 3–4 次 | 211 | 18.4 |
| 5–9 次 | 187 | 16.3 |
| 10 次以上 | 53 | 4.6 |

<details><summary>查詢語句</summary>

```sql
SELECT CASE WHEN c = 1 THEN '1 次' WHEN c = 2 THEN '2 次'
            WHEN c <= 4 THEN '3–4 次' WHEN c <= 9 THEN '5–9 次'
            ELSE '10 次以上' END AS 出現次數,
       count(*) AS 物種數,
       round(count(*) * 100.0 / sum(count(*)) OVER (), 1) AS 佔比
FROM (SELECT species_accepted, count(*) c FROM extract
      WHERE species_accepted IS NOT NULL GROUP BY 1)
GROUP BY 1 ORDER BY min(c)
```
</details>

### 科的集中度：前 10 大科佔約一半

202 個科中有 42 個只有 1 筆。分布是重尾，但不到極端集中。

| 前 N 大科 | 累計筆數 | 累計佔比 % |
| --- | --- | --- |
| 5 | 1274 | 33.0 |
| 10 | 1861 | 48.2 |
| 20 | 2403 | 62.2 |
| 50 | 3104 | 80.4 |
| 100 | 3617 | 93.7 |
| 202 | 3862 | 100.0 |

<details><summary>查詢語句</summary>

```sql
WITH f AS (SELECT family_final, count(*) AS c FROM extract
                   WHERE family_final IS NOT NULL GROUP BY 1),
     r AS (SELECT c,
                  row_number() OVER (ORDER BY c DESC) AS rn,
                  sum(c) OVER (ORDER BY c DESC ROWS UNBOUNDED PRECEDING) AS cum,
                  sum(c) OVER () AS total,
                  count(*) OVER () AS n_fam
           FROM f)
SELECT rn AS 前N大科, cum AS 累計筆數, round(cum * 100.0 / total, 1) AS 累計佔比
FROM r WHERE rn IN (5, 10, 20, 50, 100) OR rn = n_fam ORDER BY rn
```
</details>

---

## 六、資料的時效性

### 這是一份 2019-11-21 的快照

更新日期範圍 2010-10-15 ~ 2019-11-21，最新一筆距今約 6 年。

**這會改變 Phase 5「空白格推薦」的定位**：它能回答的是「2019 年以前哪些同科物種尚未收錄」，屬於歷史盤點，不是現況的市場機會。

| 年份 | 筆數 | 佔比 % |
| --- | --- | --- |
| 2010 | 9163 | 67.3 |
| 2011 | 2323 | 17.1 |
| 2012 | 206 | 1.5 |
| 2013 | 121 | 0.9 |
| 2014 | 325 | 2.4 |
| 2015 | 244 | 1.8 |
| 2016 | 414 | 3.0 |
| 2017 | 80 | 0.6 |
| 2018 | 384 | 2.8 |
| 2019 | 362 | 2.7 |

<details><summary>查詢語句</summary>

```sql
SELECT year(update_date) AS 年份, count(*) AS 筆數,
       round(count(*) * 100.0 / sum(count(*)) OVER (), 1) AS 佔比
FROM ingredient GROUP BY 1 ORDER BY 1
```
</details>

---

## 七、Function 標籤的粒度問題

### SKIN CONDITIONING 幾乎沒有區辨力

用 `SKIN CONDITIONING` 做「某用途集中在哪些科」的分析等於沒篩選——它涵蓋 181 個科、近六成的生物來源萃取物。

**Phase 5 應優先使用橫跨科數較少的標籤**，那些才有化學分類學訊號。

| 用途 | 橫跨科數 | 筆數 | 佔生物來源 % |
| --- | --- | --- | --- |
| SKIN CONDITIONING | 181 | 2276 | 58.9 |
| SKIN PROTECTING | 89 | 248 | 6.4 |
| EMOLLIENT | 84 | 282 | 7.3 |
| MASKING | 82 | 625 | 16.2 |
| ANTIOXIDANT | 70 | 216 | 5.6 |
| PERFUMING | 69 | 709 | 18.4 |
| ASTRINGENT | 68 | 218 | 5.6 |
| HUMECTANT | 65 | 146 | 3.8 |
| HAIR CONDITIONING | 65 | 194 | 5.0 |
| TONIC | 59 | 260 | 6.7 |
| ABRASIVE | 49 | 132 | 3.4 |

<details><summary>查詢語句</summary>

```sql
SELECT f AS 用途, count(DISTINCT family_final) AS 橫跨科數, count(*) AS 筆數,
       round(count(*) * 100.0 / (SELECT count(*) FROM extract), 1) AS 佔生物來源
FROM (SELECT unnest(i.functions) AS f, e.family_final
      FROM extract e JOIN ingredient i USING(ref_no) WHERE e.family_final IS NOT NULL)
GROUP BY 1 HAVING count(*) >= 100 ORDER BY 2 DESC LIMIT 12
```
</details>

---

## 八、資料品質的實際樣貌

錯誤密度不高，但**集中在最要命的欄位**——科名與學名，也就是圖譜的骨架。

| 問題 | 規模 | 說明 |
| --- | --- | --- |
| 科名寫法 | 236 種 | 對應 202 個真實的科（含錯字與舊科名） |
| 科名拼字錯誤 | 15 種 | 如 Laminaceae、Palmaceae、Zygopuhyllaceae |
| 屬名／種小名錯字 | 27 筆受影響 | 30 條修正規則，含需限定屬者 |
| INCI 與敘述矛盾 | 8 筆 | 指向兩個不同接受種，無法判定，已排除 |
| COSING 科名歸錯 | 3 組 | 最誇張者：綠藻 Ulva lactuca 被歸入莎草科 Cyperaceae |
| CAS 格式問題 | 13,622 筆 | 每一筆都有前導 U+00A0；分隔符混用三種 |

詳見 `90-Reports/cleaning-report.md` 與 `_data/corrections/`。

---

## 九、對後續 Phase 的三個判斷

1. **Phase 5 的「空白格推薦」要重新定位。** 資料停在 2019，產出應理解為歷史盤點而非現況的市場機會。

2. **法規那層比原計劃預期更有價值**，因為限制高度集中於特定科；但必須先補進 Annex 條文，光有代碼做不出解讀。

3. **Function 要分層使用。** 以 `SKIN CONDITIONING` 做關聯分析等於沒篩，應優先採用橫跨科數少的標籤。

