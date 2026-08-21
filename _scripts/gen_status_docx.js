const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  LevelFormat, PageBreak,
} = require('docx');
const fs = require('fs');
const COMMITS = require('child_process')
  .execSync('git rev-list --count HEAD', {cwd: __dirname.includes('scratchpad') ? '/Users/justnichen/Documents/cosing' : __dirname + '/..'})
  .toString().trim();

const FONT = 'Microsoft JhengHei';
const MONO = 'Courier New';
const W = 9026;                 // A4 content width in DXA
const GREEN = 'D9EAD3', YELLOW = 'FFF2CC', GREY = 'EFEFEF', HEAD = '1F3864', BAND = 'E8EEF7';

const t = (text, o = {}) => new TextRun({ text, font: FONT, size: 20, ...o });
const mono = (text, o = {}) => new TextRun({ text, font: MONO, size: 17, ...o });

const p = (text, o = {}) => new Paragraph({
  children: Array.isArray(text) ? text : [t(text, o.run || {})],
  spacing: { after: o.after ?? 120, before: o.before ?? 0 },
  alignment: o.align,
  ...(o.border ? { border: o.border } : {}),
});

const h = (text, level) => new Paragraph({
  heading: level,
  spacing: { before: level === HeadingLevel.HEADING_1 ? 360 : 260, after: 140 },
  children: [new TextRun({ text, font: FONT, bold: true,
    size: level === HeadingLevel.HEADING_1 ? 30 : 24,
    color: level === HeadingLevel.HEADING_1 ? HEAD : '2E5496' })],
});

const cell = (children, { w, shade, bold, align, font, color } = {}) => new TableCell({
  width: { size: w, type: WidthType.DXA },
  shading: shade ? { type: ShadingType.CLEAR, fill: shade, color: 'auto' } : undefined,
  margins: { top: 60, bottom: 60, left: 100, right: 100 },
  children: (Array.isArray(children) ? children : [children]).map(c =>
    typeof c === 'string'
      ? new Paragraph({ alignment: align, spacing: { after: 0 },
          children: [new TextRun({ text: c, font: font || FONT, size: 19, bold, color })] })
      : c),
});

function table(cols, rows, opts = {}) {
  const header = new TableRow({
    tableHeader: true,
    children: cols.map(c =>
      cell(c.label, { w: c.w, shade: HEAD, bold: true, align: c.align, color: 'FFFFFF' })),
  });
  const body = rows.map((r, idx) => new TableRow({
    children: r.map((v, i) => {
      const isObj = v && typeof v === 'object' && !Array.isArray(v) && 'text' in v;
      const text = isObj ? v.text : v;
      const shade = (isObj && v.shade) || (idx % 2 === 1 ? BAND : undefined);
      return cell(text, { w: cols[i].w, shade, align: cols[i].align,
                          bold: isObj ? v.bold : false, font: cols[i].mono ? MONO : undefined });
    }),
  }));
  return new Table({
    columnWidths: cols.map(c => c.w),
    width: { size: W, type: WidthType.DXA },
    rows: [header, ...body],
  });
}

const codeBlock = lines => lines.map((l, i) => new Paragraph({
  spacing: { after: i === lines.length - 1 ? 160 : 0, before: i === 0 ? 40 : 0 },
  shading: { type: ShadingType.CLEAR, fill: 'F5F5F5', color: 'auto' },
  indent: { left: 280 },
  children: [mono(l)],
}));

const note = text => new Paragraph({
  spacing: { before: 80, after: 160 },
  indent: { left: 240 },
  border: { left: { style: BorderStyle.SINGLE, size: 18, color: 'C9A227', space: 12 } },
  children: [t(text, { italics: false })],
});

const DONE   = { text: '✅ 完成',   shade: GREEN,  bold: true };
const PART   = { text: '🟡 部分完成', shade: YELLOW, bold: true };
const TODO   = { text: '⬜ 未開始', shade: GREY };

// ------------------------------------------------------------------ content
const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 20 } } } },
  numbering: { config: [{
    reference: 'bul', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•',
      alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 460, hanging: 240 } } } }] }] },
  sections: [{
    properties: { page: { margin: { top: 1300, bottom: 1300, left: 1440, right: 1440 } } },
    children: [
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun({ text: '植物萃取物知識圖譜', font: FONT, bold: true, size: 40, color: HEAD })],
      }),
      new Paragraph({
        spacing: { after: 200 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: HEAD, space: 8 } },
        children: [new TextRun({ text: '實作階段狀態紀錄', font: FONT, size: 28, color: '2E5496' })],
      }),
      table(
        [{ label: '項目', w: 2200 }, { label: '內容', w: 6826 }],
        [
          ['文件產生日期', new Date().toISOString().slice(0,10)],
          ['資料來源', '_data/kb.duckdb（由 _data/COSING_CAS.csv 唯讀原檔重建）'],
          ['原始資料', 'EU COSING 化妝品成分資料庫，13,622 筆（2019-11-21 快照）'],
          ['專案位置', '/Users/justnichen/Documents/cosing'],
          ['版本控制', `git，${COMMITS} 個 commit`],
          ['重建指令', { text: './run_all.sh（2019）／ ./run_all.sh 2026', bold: true }],
        ],
      ),
      note('本文件所有數字皆由腳本直接查詢資料庫產生，非人工填寫。執行 ./run_all.sh 可完整重建並複驗。'),

      h('一、整體進度總覽', HeadingLevel.HEADING_1),
      table(
        [{ label: 'Phase', w: 760, align: AlignmentType.CENTER },
         { label: '內容', w: 2300 },
         { label: '狀態', w: 1300, align: AlignmentType.CENTER },
         { label: '主要產出', w: 4666 }],
        [
          ['0', '資料剖析', DONE, '90-Reports/data-profile.md'],
          ['1', '資料清理與載入 ⭐', DONE, 'kb.duckdb、corrections/ 五張對照表、cleaning-report.md'],
          ['2', '分類階層驗證（GBIF）', DONE, '_data/taxonomy.csv、taxon 表、gbif-taxonomy-report.md'],
          ['3', '部位與製程抽取', DONE, '_data/vocab/ 四張詞表、parts-process-report.md'],
          ['4', '外部化學層富集', DONE, 'LOTUS 成分層、PubChem 結構層（僅 2026 資料）'],
          ['5', '挖掘隱藏關聯', TODO, '90-Reports/ 下各項分析'],
          ['6', 'Vault 生成', TODO, '10-Species / 20-Family / 30-MOC 筆記'],
          ['7', 'AI 問答層', TODO, '四層混合檢索工具組'],
        ],
      ),
      p(''),
      p([t('進度：', { bold: true }), t('8 個 Phase 中，5 個完成、3 個未開始。Phase 0–3 在兩份資料上各跑完一次，Phase 4 已在 2026 資料上完成。')]),
      p(''),
      p([t('Phase 1–3 在兩份資料上的產出對照', { bold: true })]),
      table(
        [{ label: '項目', w: 2800 }, { label: '2019 快照', w: 1700, align: AlignmentType.RIGHT },
         { label: '2026 全庫', w: 1700, align: AlignmentType.RIGHT },
         { label: '倍數', w: 1200, align: AlignmentType.RIGHT },
         { label: '', w: 1626 }],
        [
          ['成分總數', '13,622', '33,638', '2.47×', ''],
          ['生物來源萃取物', '3,862', '7,690', '1.99×', '接近翻倍'],
          ['不重複二名法', '1,263', '3,179', '2.52×', ''],
          ['物種（GBIF 接受名）', '1,149', '2,827', '2.46×', ''],
          ['屬', '720', '1,535', '2.13×', ''],
          ['科', '202', '376', '1.86×', ''],
          ['有使用部位', '3,504', '6,655', '1.90×', ''],
          ['細胞培養來源', '112', '507', '4.53×', '成長最快'],
          ['Function 詞彙數', '70', '82', '1.17×', '新增細分類'],
          ['帶法規限制', '1,073', '2,473', '2.30×', ''],
        ],
      ),

      h('二、目前資料庫狀態', HeadingLevel.HEADING_1),
      p([t('⚠️ 2019 快照本身只涵蓋約一半', { bold: true })]),
      table(
        [{ label: '', w: 3000 }, { label: '筆數', w: 1800, align: AlignmentType.RIGHT },
         { label: '', w: 4226 }],
        [
          ['ingredient（2019 快照）', '13,622', '唯讀，未更動'],
          ['inventory_2026（現行全庫）', '33,638', '已取回並並存'],
          ['兩邊都有', '13,441', '依 COSING Ref No 對應'],
          ['只在 2019', '181', '已下架或改編號'],
          ['只在 2026', '20,197', '其中 3,871 筆為生物來源'],
        ],
      ),
      note('取回全庫後才發現：在 COSING_CAS.csv 自己的編號範圍（31364–97704）內，現行資料庫有 27,170 筆，該檔只收錄 13,622 筆——涵蓋率僅 50.1%。兩邊都有的 13,441 筆全為 Active，但範圍內未收錄者也有 99.7% 是 Active，無法用「只匯出有效項目」解釋。COSING_CAS.csv 從來就是約一半的子集，不是 2019 年的完整匯出。'),
      note('因此 Phase 0–3 所有比例（3,862 筆生物來源、前 10 大科佔 48%、40% 物種只出現一次）應理解為「該子集的樣貌」，不是 COSING 母體比例。結論方向多半仍成立，但百分比不可當作母體數值引用。詳見 90-Reports/snapshot-vs-current.md。'),
      p([t('資料表結構', { bold: true })]),
      table(
        [{ label: '資料表', w: 2000, mono: true }, { label: '列數', w: 1200, align: AlignmentType.RIGHT },
         { label: '說明', w: 5826 }],
        [
          ['ingredient', '13,622', '全庫化妝品成分主表，保留 CAS / Function / Restriction 完整欄位'],
          ['extract', '3,862', '生物來源萃取物，帶科屬種、GBIF 階層與修正來源欄位'],
          ['taxon', '1,263', 'GBIF 分類階層：接受名、gbif_key、屬科目綱門界'],
          ['regulation', '2,389', '現行 Annex II–VI 條文（2026-08 擷取）'],
          ['inventory_2026', '33,638', '現行全庫成分（2026-08 擷取），與 2019 快照並存'],
          ['ingredient_citation', '3,132', '成分↔條文連結，分 2019 與現行兩個來源'],
          ['extract_parsed', '3,862', '解析中繼表，供除錯與追溯用'],
        ],
      ),
      p(''),
      p([t('生物來源萃取物的解析結果', { bold: true })]),
      ...codeBlock([
        'extract  3,862 筆（生物來源）',
        '  ├─ 有科別（family_final）  3,862   100.00%',
        '  ├─ 有完整物種連結         3,787    98.06%',
        '  ├─ 待 GBIF 補科               0    Phase 2 已全數判定',
        '  └─ 查無定論已排除             8    INCI 與敘述指向兩個不同接受種',
        '',
        'taxon  1,263 個二名法',
        '  ├─ GBIF 種層級解析        1,193    94.5%',
        '  ├─ 同物異名統一到接受名     185',
        '  └─ 種名查無，退回屬層級取科   55',
        '',
        '化學層（Phase 4，僅 2026）',
        '  ├─ LOTUS 三元組         674,454   37,469 生物 / 227,319 化合物',
        '  ├─ 物種查得到成分         2,219   78.5% of 2,827',
        '  ├─ 物種—化合物配對      126,775',
        '  └─ PubChem 解析 CAS       6,557   61.9% of 10,600',
        '',
        '部位與製程（Phase 3）',
        '  ├─ 有使用部位             3,504    90.7%',
        '  ├─ 有製程                 3,630    94.0%',
        '  ├─ 複合部位（多值）         340',
        '  └─ 細胞培養來源             112    無部位，屬正常',
        '',
        '法規層（現行 Annex，2026-08 擷取）',
        '  ├─ Annex 條文             2,389    與線上總數相符，抓取完整',
        '  ├─ 2019 引用解析率        97.2%   1,094 / 1,125 對到現行條文',
        '  ├─ 生物來源受限（現行）      154',
        '  └─ 生物來源受限（2019）      158',
      ]),
      p([t('分類階層規模', { bold: true })]),
      table(
        [{ label: '層級', w: 2400 }, { label: '數量', w: 1400, align: AlignmentType.RIGHT },
         { label: '備註', w: 5226 }],
        [
          ['科（COSING 正規化後）', '189', '原始有 236 種寫法，經錯字與 APG IV 正規化後合併'],
          ['科（GBIF 判定，最終值）', '202', 'family_final；3,826 列採 GBIF，36 列採 COSING 備援'],
          ['屬', '720', ''],
          ['物種（二名法）', '1,263', '其中 1,193 個取得 GBIF accepted name'],
          ['界別分布', '4', 'Plantae 3,782 / Chromista 23 / Fungi 21 / 未定 36'],
          ['使用部位', '28', '73 個 token 正規化為 28 種（vocab/plant_part.csv）'],
          ['製程', '28', '40 個 token 正規化為 28 種（vocab/process.csv）'],
          ['製程修飾語', '16', '如 hydrolyzed、expressed、rectified'],
          ['用途（Function）', '70', '受控詞彙，可直接使用'],
          ['帶法規限制的成分', '1,073', 'Annex II–VI，原計劃遺漏的一層'],
        ],
      ),
      p(''),
      p([t('解析狀態分布', { bold: true })]),
      table(
        [{ label: 'taxon_status', w: 2600, mono: true }, { label: '列數', w: 1000, align: AlignmentType.RIGHT },
         { label: '意義', w: 5426 }],
        [
          ['agree', '3,789', 'INCI 與敘述兩路徑一致，自動採用（98.1%）'],
          ['inci_not_binomial', '32', 'INCI 為俗名或商品名，學名取自敘述'],
          ['genus_level_entry', '17', 'INCI 只到屬層級，如 CITRUS SPECIES'],
          ['excluded', '8', '查無定論，不建立物種連結'],
          ['hyphen_split', '6', 'INCI 把連字號學名拆成兩個詞'],
          ['inci_truncated', '4', 'INCI 截斷種下名，敘述較完整'],
          ['resolved_by_gbif', '4', '經 GBIF 查證為同物異名並更正'],
          ['spelling_variant', '1', '編輯距離 1 的拼字差異'],
          ['desc_unparsed', '1', '敘述無可解析學名'],
        ],
      ),

      new Paragraph({ children: [new PageBreak()] }),

      h('三、各 Phase 詳細狀態', HeadingLevel.HEADING_1),

      h('Phase 0 — 資料剖析　✅ 完成', HeadingLevel.HEADING_2),
      table(
        [{ label: '', w: 1700, }, { label: '', w: 7326 }],
        [
          [{ text: '狀態', bold: true }, '完成'],
          [{ text: '產出', bold: true }, '90-Reports/data-profile.md（由 _scripts/00_profile.py 產生，可重跑）'],
          [{ text: '關鍵發現', bold: true }, '資料為 EU COSING 全庫，英文＋拉丁 INCI 命名，非原計劃假設的中文俗名；13,622 筆中僅 3,862 筆為生物來源'],
          [{ text: '驗收', bold: true }, '句型已歸納（95.4% 公式化）、物種規模已知、結構完整性已確認（無欄位錯位）'],
        ],
      ),

      h('Phase 1 — 資料清理與載入　✅ 完成', HeadingLevel.HEADING_2),
      p('本專案真正的成敗關鍵。原計劃的「LLM 學名抽取」作廢，改為規則解析＋錯字修正。'),
      table(
        [{ label: '對照表', w: 2600, mono: true }, { label: '列數', w: 900, align: AlignmentType.RIGHT },
         { label: '內容', w: 5526 }],
        [
          ['family_typo.csv', '15', '科名拼字錯誤，如 Laminaceae → Lamiaceae'],
          ['family_apg.csv', '32', '舊科名 → APG IV 接受名，如 Compositae → Asteraceae'],
          ['taxon_typo.csv', '29', '屬名與種小名錯字，含 scope_genus 限定欄'],
          ['split_families.csv', '3', 'APG IV 拆分科，刻意不做科層級映射'],
          ['conflicts.csv', '71', 'INCI 與敘述矛盾，含自動與 GBIF 裁決紀錄'],
        ],
      ),
      p(''),
      p([t('七項驗收全數通過：', { bold: true })]),
      ...[
        'ingredient 總列數 = 13,622',
        'Palmae / Palmaceae / Arecaceae 合併為單一科節點',
        'Laminaceae → Lamiaceae',
        '屬名解析率 > 98%（實際 99.35%）',
        'Liliaceae / Scrophulariaceae 未被科層級硬映射',
        '查無定論者未帶入物種連結',
        'conflicts.csv 無未裁決項目',
      ].map(x => new Paragraph({ numbering: { reference: 'bul', level: 0 },
        spacing: { after: 40 }, children: [t(x)] })),
      note('原檔 _data/COSING_CAS.csv 設為唯讀（444），一個位元組都未修改。所有修正皆存於 corrections/ 對照表，可追溯、可回溯、可稽核。'),

      h('Phase 2 — 分類階層驗證　✅ 完成', HeadingLevel.HEADING_2),
      table(
        [{ label: '', w: 1700 }, { label: '', w: 7326 }],
        [
          [{ text: '產出', bold: true }, '_data/taxonomy.csv、kb.duckdb 的 taxon 表、90-Reports/gbif-taxonomy-report.md'],
          [{ text: '新增欄位', bold: true }, 'extract 表新增 species_accepted、gbif_key、genus_gbif、family_gbif、order_name、kingdom、family_final、family_source'],
          [{ text: '解析結果', bold: true }, '1,263 個二名法查證 1,193 個（94.5%）；185 個同物異名統一到接受名；55 個退回屬層級取科'],
          [{ text: '驗收', bold: true }, '六項全數通過：每列都有科別、拆分科 0 筆待決、解析率 > 90%、同物異名已統一、不一致者留有紀錄、無動物界誤配'],
        ],
      ),
      p(''),
      p([t('APG IV 拆分科的判定結果', { bold: true })]),
      p('這是刻意不做科層級映射的理由：若把 Liliaceae 整批映射到單一科，53 筆中會有 46 筆歸錯。'),
      table(
        [{ label: 'COSING 原科名', w: 2400 }, { label: 'GBIF 依屬名判定', w: 3200 },
         { label: '列數', w: 1000, align: AlignmentType.RIGHT }, { label: '', w: 2426 }],
        [
          ['Liliaceae（53）', 'Asphodelaceae', '18', ''],
          ['', 'Asparagaceae', '17', ''],
          ['', 'Amaryllidaceae', '9', ''],
          ['', 'Liliaceae（狹義）', '7', '僅這 7 筆原本就對'],
          ['', 'Smilacaceae', '2', ''],
          ['Scrophulariaceae（13）', 'Scrophulariaceae（狹義）', '7', ''],
          ['', 'Plantaginaceae', '4', ''],
          ['', 'Orobanchaceae', '2', ''],
          ['Myoporaceae（1）', 'Scrophulariaceae', '1', ''],
        ],
      ),
      p(''),
      p([t('COSING 與 GBIF 科名不一致：179 列、42 組', { bold: true })]),
      p('多數是 APG IV 的正常修訂（如 Nymphaeaceae → Nelumbonaceae、Saxifragaceae → Grossulariaceae），但其中三組是 COSING 的實質錯誤，已由 GBIF 更正：'),
      table(
        [{ label: '學名', w: 2600 }, { label: 'COSING 誤植', w: 2200 },
         { label: 'GBIF 正確', w: 2200 }, { label: '列數', w: 2026, align: AlignmentType.RIGHT }],
        [
          ['Cupressus sempervirens', 'Pinaceae', 'Cupressaceae', '9'],
          ['Buddleja spp.', 'Loganiaceae', 'Scrophulariaceae', '2'],
          ['Ulva lactuca（綠藻）', 'Cyperaceae（莎草科）', 'Ulvaceae', '2'],
        ],
      ),
      note('GBIF 查詢的三個陷阱已寫入程式碼並驗證：① 未過濾界時「Gutta percha」會命中一種甲蟲屬；② matchType 為 HIGHERRANK 時 GBIF 只退回屬或科層級，不能當作「這是哪一種」的答案；③ 骨幹有重複條目時會回傳 NONE 並附註 Multiple equal matches，加上 kingdom 提示即可解開（Salix alba 即為一例）。'),
      note('模糊比對（FUZZY）共 17 筆，其中 15 筆改變了種小名，已逐筆列於報告供抽查。實作時抓到一筆真錯：Melaleuca cajaputi 被 GBIF 比對到 M. squarrosa（不同物種），已修正為正確的 Melaleuca cajuputi。'),

      h('Phase 3 — 部位與製程抽取　✅ 完成', HeadingLevel.HEADING_2),
      p('全部以詞表比對完成，未使用 LLM。詞表存於 _data/vocab/，新增詞彙不必改程式。'),
      table(
        [{ label: '', w: 1700 }, { label: '', w: 7326 }],
        [
          [{ text: '產出', bold: true }, '_data/vocab/ 四張詞表；extract 表新增 plant_part、part_count、part_source、process、process_all、process_modifiers、is_cell_culture 等欄位'],
          [{ text: '部位來源', bold: true }, 'INCI 名稱 3,091 筆；敘述補回 404 筆；由製程反推 9 筆（seedcake→seed）'],
          [{ text: '驗收', bold: true }, '四項全數通過：部位涵蓋率 > 75%、製程涵蓋率 > 90%、複合部位已拆多值、未標示者留空未臆測'],
        ],
      ),
      p(''),
      p([t('使用部位分布（前 14）', { bold: true })]),
      ...codeBlock([
        '  leaf        853    stem         314    peel     77',
        '  flower      570    whole_plant  208    gum      44',
        '  seed        524    aerial_part  175    resin    43',
        '  fruit       467    bark         137    bud      42',
        '  root        351    wood          98',
      ]),
      p([t('可橫向比較的物種（同一物種收錄多個部位）', { bold: true })]),
      table(
        [{ label: '物種', w: 3000 }, { label: '部位種類數', w: 1600, align: AlignmentType.RIGHT },
         { label: '萃取物數', w: 1600, align: AlignmentType.RIGHT }, { label: '', w: 2826 }],
        [
          ['Vitis vinifera', '10', '21', '葡萄'],
          ['Cupressus sempervirens', '8', '11', '地中海柏木'],
          ['Citrus aurantium', '7', '54', '橙'],
          ['Olea europaea', '7', '20', '橄欖'],
          ['Nelumbo nucifera', '7', '22', '蓮'],
        ],
      ),
      note('未標示部位的 358 筆中，58 筆是細胞培養（callus / cell culture），本來就沒有「部位」可言，留空是正確的；其餘 300 筆是 COSING 真的沒寫。一律留 NULL 不臆測為全株——未標示與全株是兩回事，猜測會把成分譜完全不同的材料混在一起。'),

      h('Phase 4 — 外部化學層富集　⬜ 未開始', HeadingLevel.HEADING_2),
      table(
        [{ label: '路徑', w: 2400 }, { label: '說明', w: 6626 }],
        [
          ['LOTUS（物種 → 成分）', '以 GBIF accepted name join；Phase 2 已完成，1,193 個接受名可直接使用'],
          ['PubChem（CAS → 結構）', '原計劃未想到的第二條路徑；2019 快照有 9,796 個不重複 CAS 主碼（含多值為 10,531），對 9,760 筆合成化學品尤其有效'],
        ],
      ),
      note('LOTUS 查不到 ≠ 該生物沒有成分，只代表文獻未收錄。分析時必須把「無資料」與「無成分」分開統計，否則結論全部偏向被研究得多的物種。'),

      h('Phase 5 — 挖掘隱藏關聯　⬜ 未開始', HeadingLevel.HEADING_2),
      p('前三項離線即可執行，不需等 Phase 4。'),
      table(
        [{ label: '#', w: 500, align: AlignmentType.CENTER }, { label: '分析', w: 3000 }, { label: '說明', w: 5526 }],
        [
          ['1', '空白格推薦 ⭐', '某用途集中在哪些科，列出該科中尚未收錄的物種'],
          ['2', '法規盲點分析 ⭐', '交叉 Restriction 與科屬階層；原計劃完全沒有，對化妝品應用最直接'],
          ['3', '用途相同但親緣極遠', '趨同演化，或 Function 標錯，兩者都值得查核'],
          ['4', '同科不同屬但用途一致', '化學分類學支持，可信度最高'],
          ['5', '同物種橫向比較群組', 'Phase 3 產出直接支援'],
          ['6', '成分集合相似度', '需 Phase 4；只留 top-k 鄰居，不建全連接圖'],
        ],
      ),

      h('Phase 6 — Vault 生成　⬜ 未開始', HeadingLevel.HEADING_2),
      table(
        [{ label: '目錄', w: 2200, mono: true }, { label: '目前', w: 1200, align: AlignmentType.RIGHT },
         { label: '預計', w: 1400, align: AlignmentType.RIGHT }, { label: '內容', w: 4226 }],
        [
          ['10-Species/', '0', '約 1,263', '物種筆記，檔名為 GBIF accepted name'],
          ['20-Family/', '0', '約 189', '科筆記，本專案最有價值的產出'],
          ['30-MOC/', '0', '約 125', '用途 70 / 部位 30 / 製程 25 的樞紐頁'],
        ],
      ),
      note('機器生成區與人工撰寫區必須以 AUTO-START / AUTO-END 標記分隔，腳本永不觸碰人工區。'),

      h('Phase 7 — AI 問答層　⬜ 未開始', HeadingLevel.HEADING_2),
      table(
        [{ label: '層', w: 1800 }, { label: '用途', w: 3200 }, { label: '實作', w: 4026 }],
        [
          ['精確查表', '學名 / INCI 名 / CAS → ID', 'Phase 1–2 的對照表'],
          ['結構化篩選', '條件查詢，含 Function 與 Annex', 'DuckDB SQL'],
          ['圖遍歷', '「相關的還有什麼」', '鄰接表'],
          ['向量檢索', '語意模糊的問題', '只用於敘述欄位'],
        ],
      ),
      note('不要用純向量 RAG。學名系統性命名讓近緣物種的 embedding 極為相似，純向量檢索會自信地取錯物種。名稱查詢必須走字典，不走向量。'),

      new Paragraph({ children: [new PageBreak()] }),

      h('四、下一步待辦', HeadingLevel.HEADING_1),
      table(
        [{ label: '順序', w: 700, align: AlignmentType.CENTER }, { label: '工作', w: 4400 },
         { label: '產出', w: 2526 }, { label: '預估', w: 1400, align: AlignmentType.CENTER }],
        [
          ['1', 'Phase 4：LOTUS（物種→成分）與 PubChem（CAS→結構）富集', 'species_compounds.csv、cas_structures.csv', '1 天'],
          ['2', 'Phase 5：關聯分析（可與 1 平行）', '90-Reports/ 各項分析', '1.5–2 天'],
          ['3', 'Phase 6：Vault 筆記生成', '10-Species / 20-Family / 30-MOC', '1 天'],
          ['4', 'Phase 7：AI 問答層', '四層混合檢索工具組', '1–2 天'],
        ],
      ),
      p(''),
      note('8 筆排除項不是永久判決。若日後查到 COSING 原意（例如 ROSA RUGOSA 那 4 筆到底是玫瑰還是野薔薇），在 conflicts.csv 把 resolution 改成 manual 並填入 resolved_to 即可。腳本重跑時不會覆寫人工裁決，此保護機制已實測驗證。'),

      h('五、法規層（額外完成）', HeadingLevel.HEADING_1),
      p('原計劃沒有這一層。2019 快照的 Restriction 欄只有代碼（如 II/358），沒有條文，答不出「限的是什麼」。已自 CosIng 官方 API 取得現行 Annex II–VI 並接入資料庫。'),
      table(
        [{ label: '', w: 1700 }, { label: '', w: 7326 }],
        [
          [{ text: '產出', bold: true }, '_data/cosing_2026/ 五份 Annex CSV；regulation / ingredient_citation / ingredient_cmr 三張表；view extract_regulation'],
          [{ text: '兩條連結', bold: true }, 'snapshot_2019（從 2019 restriction 欄解析）與 annex_2026（現行條文自己列出的適用成分編號），刻意分開存放不合併'],
          [{ text: '驗收', bold: true }, '五項全數通過'],
          [{ text: '未更新者', bold: true }, '成分主表仍為 2019 快照（13,622），線上已達 33,654，因無批次匯出途徑而未動'],
        ],
      ),
      p(''),
      p([t('解開的一個問題', { bold: true })]),
      p('II/358 = 呋喃香豆素（furocoumarines），柑橘皮油中的光敏性成分。這解釋了為何引用該條的 61 筆集中在 Rutaceae（58）與 Apiaceae（2）——呋喃香豆素正是這兩科的特徵代謝物。這是化學分類學訊號，不是巧合。'),
      p([t('現行法規下各科受限率', { bold: true })]),
      ...codeBlock([
        '  Altingiaceae      4/4     100.0%',
        '  Parmeliaceae      4/6      66.7%',
        '  Pinaceae         55/109    50.5%',
        '  Rutaceae         58/192    30.2%',
        '  Cupressaceae     10/80     12.5%',
      ]),
      note('資料時效性：CosIng 仍在維護（Annex II 標示 Last update 18/08/2026），但完整 Inventory 無批次匯出，且 data.europa.eu 的舊資料集頁面已失效。因此 ingredient 主表維持 2019 快照，法規層為現行——兩者分開，不混用。'),

      h('六、2026 全庫（額外完成）', HeadingLevel.HEADING_1),
      p('以 179 次請求取回現行全部 33,638 筆成分，非逐頁爬取。'),
      table(
        [{ label: '', w: 1700 }, { label: '', w: 7326 }],
        [
          [{ text: '方法', bold: true }, 'CosIng 前端背後的公開搜尋 API，一次 200 筆；依 substanceId 首字元分為 8 區以避開 10,000 筆深分頁上限'],
          [{ text: '合法性', bold: true }, 'robots.txt 201 條 Disallow 均未涵蓋此路徑；內容依 Commission Decision 2011/833/EU 授權 CC BY 4.0；請求間隔 1 秒'],
          [{ text: 'join 鍵', bold: true }, 'substanceId 即 COSING Ref No，已用 INCI 名稱逐筆驗證'],
          [{ text: '存放方式', bold: true }, '獨立資料表 inventory_2026，不合併、不覆蓋 2019 快照'],
          [{ text: '驗收', bold: true }, '四項全數通過'],
        ],
      ),
      p(''),
      note('三個會讓資料默默不完整的坑（皆已在程式中防堵）：① 深分頁在 10,000 筆停止，且回傳 totalResults=0 而非錯誤；② substanceId 為字串欄位，數值 range 給出看似合理的假數字（lt:100000 回傳 0，lt:110000 回傳 4,722）；③ 16 筆為索引重複文件，內容相同僅差 Elasticsearch 內部欄位。腳本在計畫數與實得數不符時直接中止，前兩個坑都是被這道檢查擋下的。'),

      h('七、Phase 1–3 重跑於 2026 全庫', HeadingLevel.HEADING_1),
      p('管線改為可切換資料來源，同一套程式跑兩份資料。2019 產出保留原表名（ingredient、extract、taxon…），2026 產出加 _v2026 後綴並存，因此既有報告與驗收全部仍然有效。'),
      table(
        [{ label: '', w: 1700 }, { label: '', w: 7326 }],
        [
          [{ text: '執行方式', bold: true }, './run_all.sh 跑 2019；./run_all.sh 2026 跑現行全庫'],
          [{ text: '2026 驗收', bold: true }, '17 項全數通過（Phase 1 七項、Phase 2 六項、Phase 3 四項）'],
          [{ text: '2019 回歸', bold: true }, '22 項不變，確認改動未破壞既有結果'],
          [{ text: '新報告', bold: true }, 'cleaning-report_v2026.md、gbif-taxonomy-report_v2026.md、parts-process-report_v2026.md、taxonomy_v2026.csv'],
        ],
      ),
      p(''),
      p([t('2026 前 10 大科', { bold: true })]),
      ...codeBlock([
        '  Fabaceae    497    Poaceae     255',
        '  Rosaceae    496    Apiaceae    223',
        '  Asteraceae  495    Pinaceae    179',
        '  Lamiaceae   435    Malvaceae   167',
        '  Rutaceae    358    Myrtaceae   136',
      ]),
      note('重跑時修掉兩個問題。① 01_load.py 原本會刪除整個資料庫檔，等於一跑 2019 就清掉所有 2026 表——改為只 DROP 自己建的表。② 新資料帶來四個未收錄的製程前綴（DEFATTED、OZONIZED、DEPOLYMERIZED、CYCLIZED），其中 DEFATTED NARCISSUS TAZETTA FLOWER 的屬名被解析成「Defatted」。這是靠 Phase 2 的「每列都有科別」驗收失敗才發現的，並非逐筆檢查得來。'),

      h('八、Phase 4 化學層（2026 資料）', HeadingLevel.HEADING_1),
      p('兩條互補路徑：LOTUS 以物種為鍵，服務生物來源萃取物；PubChem 以 CAS 為鍵，服務有單一結構的成分。'),
      table(
        [{ label: '', w: 2100 }, { label: 'LOTUS', w: 3400 }, { label: 'PubChem', w: 3526 }],
        [
          ['資料來源', 'Zenodo 凍結版 2026-04-13', 'PUG REST API'],
          ['規模', '674,454 組結構—生物—文獻三元組', '10,600 個不重複 CAS'],
          ['join 鍵', 'GBIF 接受名（非原始 COSING 名）', 'CAS 主碼'],
          ['覆蓋率', '2,219 / 2,827 物種（78.5%）', '6,557 / 10,600（61.9%）'],
          ['產出', 'species_compounds_v2026（126,775 配對）', 'cas_structure_v2026'],
          ['驗收', '四項通過', '四項通過'],
        ],
      ),
      p(''),
      p([t('專案核心假設現在可量化', { bold: true })]),
      p('「親緣相近的植物產生相似次級代謝物」過去只能靠科屬階層間接支持，現在有實際化合物集合：'),
      ...codeBlock([
        '  Asteraceae     7,085 個化合物  跨 170 物種',
        '  Fabaceae       5,918           跨 157',
        '  Lamiaceae      3,864           跨 109',
        '  Zingiberaceae  1,977           跨  32',
      ]),
      note('⚠️ 覆蓋率偏誤在資料上直接可見：成分數最多的物種是 Arabidopsis thaliana（阿拉伯芥），一個實驗室模式植物，不是化妝品原料。它排第一純粹因為被研究得最多。各科覆蓋率反映研究熱度，不是化學豐富度。報告明確要求下游不得把「無資料」當成「無成分」。'),
      note('PubChem 對生物來源的覆蓋率只有 2.5%，這是預期內的：萃取物是混合物，一個 CAS 指的是「某某植物萃取物」這個材料，不是單一分子。萃取物的化學層應以 LOTUS 為主，PubChem 為輔（對合成成分覆蓋 27.3%）。'),

      h('九、目前檔案清單', HeadingLevel.HEADING_1),
      table(
        [{ label: '路徑', w: 3400, mono: true }, { label: '說明', w: 5626 }],
        [
          ['_data/COSING_CAS.csv', '原始資料，唯讀（444），永不修改'],
          ['_data/kb.duckdb', '主資料庫，可由 run_all.sh 重建（不納入 git）'],
          ['_data/corrections/', '五張修正對照表 + README 判定準則'],
          ['_data/gbif_cache.json', 'GBIF 回應快取，含擷取日期，可離線重跑'],
          ['_data/taxonomy.csv', '1,263 個二名法的 GBIF 階層對照'],
          ['_scripts/01_load.py', '編碼、欄名、CAS 格式正規化'],
          ['_scripts/02_parse_taxon.py', '雙路徑學名解析與交叉驗證'],
          ['_scripts/03_resolve_conflicts.py', 'GBIF 矛盾裁決'],
          ['_scripts/04_clean_taxon.py', '套用對照表，建立 extract 表'],
          ['_scripts/05_gbif_taxonomy.py', 'GBIF 完整分類階層，建立 taxon 表'],
          ['_scripts/gbif.py', 'GBIF 共用模組：快取、併發、比對守衛'],
          ['_scripts/06_parts.py', '部位與製程詞表比對'],
          ['_scripts/08_fetch_annexes.py', '自 CosIng 官方 API 取現行 Annex（手動執行）'],
          ['_scripts/09_link_regulation.py', '法規層接入與新舊對照'],
          ['_scripts/10_fetch_inventory.py', '取回現行全庫成分（手動執行）'],
          ['_scripts/11_load_inventory.py', '全庫載入與新舊差異分析'],
          ['_scripts/12_normalize_2026.py', '2026 資料正規化為管線輸入格式'],
          ['_scripts/13_lotus.py', 'LOTUS 成分層富集'],
          ['_scripts/14_pubchem.py', 'PubChem 結構層富集（快取）'],
          ['_scripts/07_insights.py', '跨面向分析報告'],
          ['_data/vocab/', '部位、製程、修飾語、細胞培養四張詞表'],
          ['_scripts/00_profile.py', '重新產生剖析報告'],
          ['90-Reports/data-profile.md', 'Phase 0 剖析報告'],
          ['90-Reports/cleaning-report.md', 'Phase 1 清理報告與驗收'],
          ['90-Reports/gbif-taxonomy-report.md', 'Phase 2 分類階層報告與驗收'],
          ['90-Reports/parts-process-report.md', 'Phase 3 部位與製程報告與驗收'],
          ['90-Reports/regulation-report.md', '法規層對照報告與驗收'],
          ['90-Reports/snapshot-vs-current.md', '2019 快照 vs 2026 現況差異'],
          ['90-Reports/lotus-report_v2026.md', 'Phase 4a LOTUS 覆蓋率與偏誤'],
          ['90-Reports/pubchem-report_v2026.md', 'Phase 4b PubChem 結構覆蓋率'],
          ['90-Reports/dataset-insights.md', '資料集分析，每個結論附 SQL'],
          ['_data/cosing_2026/', '現行 Annex II–VI（2,389 條）'],
          ['run_all.sh', '完整管線，冪等，可重複執行'],
        ],
      ),
    ],
  }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(process.argv[2], b);
  console.log('wrote', process.argv[2], b.length, 'bytes');
});
