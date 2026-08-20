const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  LevelFormat, PageBreak,
} = require('docx');
const fs = require('fs');

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
          ['文件產生日期', '2026-08-14'],
          ['資料來源', '_data/kb.duckdb（由 _data/COSING_CAS.csv 唯讀原檔重建）'],
          ['原始資料', 'EU COSING 化妝品成分資料庫，13,622 筆'],
          ['專案位置', '/Users/justnichen/Documents/cosing'],
          ['版本控制', 'git，4 個 commit，最新 37611c2'],
          ['重建指令', { text: './run_all.sh', bold: true }],
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
          ['2', '分類階層驗證（GBIF）', PART, '已建 GBIF 查詢基礎設施；_data/taxonomy.csv 尚未產出'],
          ['3', '部位與製程抽取', TODO, '主表新增 plant_part / process 欄'],
          ['4', '外部化學層富集', TODO, 'species_compounds.csv、cas_structures.csv'],
          ['5', '挖掘隱藏關聯', TODO, '90-Reports/ 下各項分析'],
          ['6', 'Vault 生成', TODO, '10-Species / 20-Family / 30-MOC 筆記'],
          ['7', 'AI 問答層', TODO, '四層混合檢索工具組'],
        ],
      ),
      p(''),
      p([t('進度：', { bold: true }), t('8 個 Phase 中，2 個完成、1 個部分完成、5 個未開始。必做骨幹 Phase 0–1 已完成，Phase 2 進行中。')]),

      h('二、目前資料庫狀態', HeadingLevel.HEADING_1),
      p([t('資料表結構', { bold: true })]),
      table(
        [{ label: '資料表', w: 2000, mono: true }, { label: '列數', w: 1200, align: AlignmentType.RIGHT },
         { label: '說明', w: 5826 }],
        [
          ['ingredient', '13,622', '全庫化妝品成分主表，保留 CAS / Function / Restriction 完整欄位'],
          ['extract', '3,862', '生物來源萃取物，帶科屬種與修正來源欄位'],
          ['extract_parsed', '3,862', '解析中繼表，供除錯與追溯用'],
        ],
      ),
      p(''),
      p([t('生物來源萃取物的解析結果', { bold: true })]),
      ...codeBlock([
        'extract  3,862 筆（生物來源）',
        '  ├─ 有完整物種連結   3,787   98.06%',
        '  ├─ 待 GBIF 補科        67   APG IV 拆分科，需逐屬判定',
        '  └─ 查無定論已排除       8   INCI 與敘述指向兩個不同接受種',
      ]),
      p([t('分類階層規模', { bold: true })]),
      table(
        [{ label: '層級', w: 2400 }, { label: '數量', w: 1400, align: AlignmentType.RIGHT },
         { label: '備註', w: 5226 }],
        [
          ['科（正規化後）', '189', '原始有 236 種寫法，經錯字與 APG IV 正規化後合併'],
          ['屬', '720', ''],
          ['物種（二名法）', '1,263', 'Phase 2 需逐一取 GBIF accepted name'],
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

      h('Phase 2 — 分類階層驗證　🟡 部分完成', HeadingLevel.HEADING_2),
      table(
        [{ label: '', w: 1700 }, { label: '', w: 7326 }],
        [
          [{ text: '已完成', bold: true }, '_scripts/03_resolve_conflicts.py 已建；GBIF 查詢基礎設施完備（回應快取、界別過濾、HIGHERRANK 拒絕）；已查證 28 個名稱，裁決 12 筆矛盾'],
          [{ text: '未完成', bold: true }, '① 擴大查詢至全部 1,263 個物種　② 解決 67 筆 family_needs_gbif　③ 產出 _data/taxonomy.csv'],
          [{ text: '缺少欄位', bold: true }, 'extract 表目前無 gbif_key、order、kingdom，分類階層尚未真正接上'],
          [{ text: '預估', bold: true }, '約半天；1,263 次 API 呼叫含禮貌延遲約 10 分鐘'],
        ],
      ),
      note('GBIF 查詢的兩個陷阱已寫入程式碼並驗證：未過濾界時「Gutta percha」會命中一種甲蟲屬；matchType 為 HIGHERRANK 時 GBIF 只退回屬或科層級，不能當作「這是哪一種」的答案。'),

      h('Phase 3 — 部位與製程抽取　⬜ 未開始', HeadingLevel.HEADING_2),
      p('可直接用字典比對，不需 LLM。部位與製程就是 INCI 名稱中的固定 token。'),
      ...codeBlock([
        '部位 token 實測分布（約 30 詞）',
        '  LEAF 813  FLOWER 537  FRUIT 415  SEED 414  ROOT 339',
        '  STEM 230  BARK 129   JUICE 115  HERB 100  WOOD  88 ...',
        '  759 筆無部位 token，屬全株或未指定',
        '',
        '製程 token（約 25 詞）',
        '  EXTRACT 2219  OIL 664  POWDER 259  WATER 232  JUICE 115 ...',
      ]),

      h('Phase 4 — 外部化學層富集　⬜ 未開始', HeadingLevel.HEADING_2),
      table(
        [{ label: '路徑', w: 2400 }, { label: '說明', w: 6626 }],
        [
          ['LOTUS（物種 → 成分）', '以 GBIF accepted name join，需先完成 Phase 2'],
          ['PubChem（CAS → 結構）', '原計劃未想到的第二條路徑；10,008 個唯一 CAS 可直接換結構，對 9,760 筆合成化學品尤其有效'],
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
          ['1', '擴大 GBIF 查詢至 1,263 個物種，取 accepted name 與完整階層', '_data/taxonomy.csv', '0.5 天'],
          ['2', '解決 67 筆 APG IV 拆分科（依屬名逐一判定）', 'family_accepted 補齊', '含於上'],
          ['3', '部位與製程抽取', 'plant_part / process 欄', '0.5 天'],
          ['4', 'LOTUS 與 PubChem 富集', 'species_compounds.csv', '1 天'],
          ['5', '關聯分析（可與 4 平行）', '90-Reports/ 各項分析', '1.5–2 天'],
        ],
      ),
      p(''),
      note('8 筆排除項不是永久判決。若日後查到 COSING 原意（例如 ROSA RUGOSA 那 4 筆到底是玫瑰還是野薔薇），在 conflicts.csv 把 resolution 改成 manual 並填入 resolved_to 即可。腳本重跑時不會覆寫人工裁決，此保護機制已實測驗證。'),

      h('五、目前檔案清單', HeadingLevel.HEADING_1),
      table(
        [{ label: '路徑', w: 3400, mono: true }, { label: '說明', w: 5626 }],
        [
          ['_data/COSING_CAS.csv', '原始資料，唯讀（444），永不修改'],
          ['_data/kb.duckdb', '主資料庫，可由 run_all.sh 重建（不納入 git）'],
          ['_data/corrections/', '五張修正對照表 + README 判定準則'],
          ['_data/gbif_cache.json', 'GBIF 回應快取，含擷取日期，可離線重跑'],
          ['_scripts/01_load.py', '編碼、欄名、CAS 格式正規化'],
          ['_scripts/02_parse_taxon.py', '雙路徑學名解析與交叉驗證'],
          ['_scripts/03_resolve_conflicts.py', 'GBIF 矛盾裁決'],
          ['_scripts/04_clean_taxon.py', '套用對照表，建立 extract 表'],
          ['_scripts/00_profile.py', '重新產生剖析報告'],
          ['90-Reports/data-profile.md', 'Phase 0 剖析報告'],
          ['90-Reports/cleaning-report.md', 'Phase 1 清理報告與驗收'],
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
