import { test } from 'node:test';
import assert from 'node:assert/strict';
import { loadExplorer, readData, sleep } from './helpers.mjs';

const CAFFEINE = 'RYYVLZVUVIJVGH-UHFFFAOYSA-N';
const QUERCETIN = 'REFJWTPEDVJJIY-UHFFFAOYSA-N';

async function withExplorer(opts, fn) {
  const ex = await loadExplorer(opts);
  try {
    await fn(ex);
    assert.deepEqual(ex.errors, [], 'page reported script errors');
  } finally {
    ex.close();
  }
}

test('I18N: zh, en and ja define the same keys with no empty values', () =>
  withExplorer({}, ex => {
    const keys = l => ex.get(`Object.keys(I18N.${l}).sort()`);
    assert.deepEqual(keys('en'), keys('zh'));
    assert.deepEqual(keys('ja'), keys('zh'));
    for (const l of ['zh', 'en', 'ja']) {
      const empty = ex.get(`Object.entries(I18N.${l}).filter(([k, v]) => k !== 'cbShowing' && !v).map(([k]) => k)`);
      assert.deepEqual(empty, [], `${l} has empty strings`);
    }
  }));

test('language defaults to zh and follows localStorage and ?lang=', async () => {
  await withExplorer({}, ex => assert.equal(ex.get('LANG'), 'zh'));
  await withExplorer({ stored: 'ja' }, ex => assert.equal(ex.get('LANG'), 'ja'));
  await withExplorer({ stored: 'xx' }, ex => assert.equal(ex.get('LANG'), 'zh'));
  await withExplorer({ stored: 'zh', query: '?lang=en' }, ex => {
    assert.equal(ex.get('LANG'), 'en');
    assert.equal(ex.window.localStorage.getItem('lang'), 'zh', '?lang= must not overwrite the saved choice');
  });
});

test('language button cycles zh -> en -> ja -> zh and updates the page', () =>
  withExplorer({}, ex => {
    const btn = ex.document.getElementById('langBtn');
    const seen = [];
    for (let i = 0; i < 3; i++) {
      btn.click();
      seen.push([ex.get('LANG'), ex.document.documentElement.lang, btn.textContent, ex.window.localStorage.getItem('lang')]);
    }
    assert.deepEqual(seen, [
      ['en', 'en', '日', 'en'],
      ['ja', 'ja', '中', 'ja'],
      ['zh', 'zh-Hant', 'EN', 'zh'],
    ]);
    ex.window.setLang('ja');
    assert.equal(ex.document.title, '化粧品成分エクスプローラー');
  }));

test('species, family and compound names follow the language with the documented fallbacks', () =>
  withExplorer({}, ex => {
    const names = lang => {
      ex.window.setLang(lang);
      return ex.get(`({ sp: spName('Lavandula angustifolia'), fam: famName('Lamiaceae'), cpd: cpdName(D.ci['${CAFFEINE}']) })`);
    };
    assert.deepEqual(names('zh'), { sp: '狹葉薰衣草', fam: '唇形科', cpd: '咖啡因' });
    assert.deepEqual(names('en'), { sp: 'English lavender', fam: 'Mint family', cpd: 'caffeine' });
    assert.deepEqual(names('ja'), { sp: '真正ラベンダー', fam: 'シソ科', cpd: 'カフェイン' });

    // a compound with English and Chinese names but no Japanese one shows the English name
    const noJa = ex.get(`(() => { const c = Object.values(D.ci).find(c => c.nm && c.nm.en && c.nm.zh && !c.nm.ja); return { en: c.nm.en[0], zh: c.nm.zh[0] }; })()`);
    ex.window.setLang('ja');
    assert.equal(ex.get(`cpdName(Object.values(D.ci).find(c => c.nm && c.nm.en && c.nm.zh && !c.nm.ja))`), noJa.en);
    assert.notEqual(noJa.en, noJa.zh);

    // ja falls back to English, never to Chinese; zh does not fall back at all
    ex.get(`delete D.sp_ja['Lavandula angustifolia']`);
    assert.equal(ex.get(`spName('Lavandula angustifolia')`), 'English lavender');
    ex.get(`delete D.sp_en['Lavandula angustifolia']`);
    assert.equal(ex.get(`spName('Lavandula angustifolia')`), '');
    ex.window.setLang('zh');
    ex.get(`delete D.sp_zh['Lavandula angustifolia']`);
    assert.equal(ex.get(`spName('Lavandula angustifolia')`), '');
  }));

test('search finds compounds by English, Chinese and Japanese name', () =>
  withExplorer({}, async ex => {
    const hasCompound = (rows, formula) => rows.some(r => r.includes('化合物') && r.includes(formula));
    assert.ok(hasCompound(await ex.search('caffeine'), 'C8H10N4O2'));
    assert.ok(hasCompound(await ex.search('咖啡因'), 'C8H10N4O2'));
    assert.ok(hasCompound(await ex.search('ケルセチン'), 'C15H10O7'));
    assert.ok(hasCompound(await ex.search('槲皮素'), 'C15H10O7'));
  }));

test('search keeps room for compounds even when many ingredients match', () =>
  withExplorer({}, async ex => {
    const rows = await ex.search('caffeine');
    assert.ok(rows.length <= 15);
    assert.ok(rows.filter(r => r.includes('化合物')).length >= 1);
  }));

test('search matches Japanese species and family names (results show the active language)', () =>
  withExplorer({ query: '?lang=ja' }, async ex => {
    assert.ok((await ex.search('ラベンダー')).some(r => r.startsWith('Lavandula angustifolia') && r.includes('真正ラベンダー')));
    assert.ok((await ex.search('バラ科')).some(r => r.startsWith('Rosaceae')));
  }));

test('compound panel lists names in three languages plus aliases', () =>
  withExplorer({}, async ex => {
    ex.window.navToCompound(CAFFEINE);
    const panel = ex.document.getElementById('panel').textContent;
    assert.match(panel, /caffeine\s*\|\s*咖啡因\s*\|\s*カフェイン/);
    assert.match(panel, /別名/);
    assert.match(panel, /194\.19/);
  }));

test('compound browser filters by LogP, MW and name, and sorts', () =>
  withExplorer({}, ex => {
    ex.window.openCompoundBrowser();
    const total = ex.get('CB.filtered.length');
    assert.equal(total, ex.get('Object.keys(D.ci).length'));

    const expectLogp = ex.get(`Object.values(D.ci).filter(c => c.desc && c.desc[0] >= 2 && c.desc[0] <= 5).length`);
    ex.window.cbSetNum('minLogp', '2');
    ex.window.cbSetNum('maxLogp', '5');
    assert.equal(ex.get('CB.filtered.length'), expectLogp);
    assert.ok(expectLogp > 0 && expectLogp < total);

    ex.window.cbClearFilters();
    ex.window.cbSetQuery('ケルセチン');
    const hits = ex.get(`CB.filtered.map(([ik]) => ik)`);
    assert.ok(hits.includes(QUERCETIN));

    ex.window.cbClearFilters();
    ex.window.cbSetSort('mw');
    const mws = ex.get(`CB.filtered.slice(0, 50).map(([, c]) => c.mw || 0)`);
    assert.deepEqual(mws, [...mws].sort((a, b) => b - a));
  }));

test('Help text renders in every language without falling back to another', () =>
  withExplorer({}, ex => {
    const heading = l => { ex.window.setLang(l); return ex.document.querySelector('#helpBox h2').textContent; };
    assert.equal(heading('zh'), '使用說明');
    assert.equal(heading('en'), 'Help');
    assert.equal(heading('ja'), '使い方');
    assert.match(ex.document.getElementById('helpBox').textContent, /ノードの種類/);
  }));

const SC = readData('species_compounds.json');

test('every species lists all of its shared compounds, not just those in the first 30 species of each compound', () =>
  withExplorer({}, ex => {
    for (const sp of ['Vitis vinifera', 'Zingiber officinale', 'Solanum lycopersicum']) {
      assert.equal(ex.get(`D.ci_by_sp['${sp}'].length`), SC.shared[sp].length, sp);
      assert.ok(SC.shared[sp].length > 300, `${sp} should have hundreds of shared compounds`);
    }
    const fam = ex.get(`D.sp_fam['Vitis vinifera']`);
    const expected = new Set(Object.entries(SC.shared).filter(([sp]) => ex.get(`D.sp_fam[${JSON.stringify(sp)}]`) === fam).flatMap(([, v]) => v));
    assert.equal(ex.get(`D.ci_by_fam[${JSON.stringify(fam)}].length`), expected.size, 'family index follows the same lists');
  }));

test('a species with only species-specific compounds offers them on demand and each opens with full details', () =>
  withExplorer({}, async ex => {
    const sp = 'Drimia maritima';
    assert.equal(ex.get(`D.ci_by_sp['${sp}']`), undefined, 'precondition: no shared compound');
    const n = SC.own_n[sp];
    assert.ok(n > 24, 'precondition: more than one page');

    ex.window.eval(`GRAPH = buildEgoGraph('species', '${sp}'); selectedNode = GRAPH.nodes[0]; showPanel(selectedNode)`);
    const sec = ex.document.getElementById('own-sec');
    assert.match(sec.querySelector('h3').textContent, new RegExp(`\\(${n}\\)`));
    assert.equal(ex.document.querySelectorAll('#own-grid .sp-chem-card').length, 0, 'nothing loads before the click');

    ex.document.getElementById('own-btn').click();
    await sleep(300);
    assert.equal(ex.document.querySelectorAll('#own-grid .sp-chem-card').length, 24);
    assert.equal(ex.document.getElementById('own-btn'), null);
    ex.document.getElementById('own-more').click();
    await sleep(100);
    assert.equal(ex.document.querySelectorAll('#own-grid .sp-chem-card').length, 48);

    ex.document.querySelector('#own-grid .sp-chem-card').click();
    const panel = ex.document.getElementById('panel').textContent;
    assert.match(panel, /物化性質/);
    assert.match(panel, /LogP/);
    assert.ok(ex.document.querySelector('#panel a[href^="https://pubchem.ncbi.nlm.nih.gov/compound/"]'), 'PubChem link uses the CID');
    assert.match(ex.get('GRAPH.nodes[0].label'), /^C\d/);
    await sleep(300);
  }));

test('the ingredient panel of such a species shows the species-specific section instead of an empty compound grid', () =>
  withExplorer({}, async ex => {
    const ref = ex.get(`Object.keys(D.items).find(k => D.items[k].sp === 'Drimia maritima')`);
    ex.window.eval(`GRAPH = buildEgoGraph('ingredient', '${ref}'); selectedNode = GRAPH.nodes[0]; showPanel(selectedNode)`);
    const panel = ex.document.getElementById('panel');
    assert.ok(panel.querySelector('#own-sec'));
    assert.equal(panel.querySelectorAll('.sp-chem-card').length, 0);
    assert.equal(ex.get(`GRAPH.nodes.filter(n => n.type === 'compound').length`), 0, 'graph shows no compound without data');
    await sleep(100);
  }));

test('species-specific section follows the language', () =>
  withExplorer({ query: '?lang=ja' }, async ex => {
    ex.window.eval(`GRAPH = buildEgoGraph('species', 'Drimia maritima'); selectedNode = GRAPH.nodes[0]; showPanel(selectedNode)`);
    assert.match(ex.document.querySelector('#own-sec h3').textContent, /この種にのみ見られる化合物/);
    assert.equal(ex.document.getElementById('own-btn').textContent, '表示');
    await sleep(100);
  }));

test('structure lookup falls back to the add-on layer and treats its absence as normal', () =>
  withExplorer({}, async ex => {
    const calls = [];
    ex.window.fetch = async url => {
      calls.push(url);
      if (url === 'svg/AB.json') return { ok: true, json: async () => ({ ABMAIN: 'main-drawing' }) };
      if (url === 'svg/add/AB.json') return { ok: true, json: async () => ({ ABLATE: 'late-drawing' }) };
      return { ok: false, status: 404 };
    };
    ex.window.eval('decompressSvg = async b => "SVG:" + b');
    assert.equal(await ex.window.getSvg('ABMAIN'), 'SVG:main-drawing');
    assert.equal(await ex.window.getSvg('ABLATE'), 'SVG:late-drawing');
    assert.equal(await ex.window.getSvg('ABNONE'), null);
    // a prefix without an add-on file: the main chunk still answers, and the 404 is asked about once
    assert.equal(await ex.window.getSvg('CDGONE'), null);
    assert.equal(await ex.window.getSvg('CDGONE'), null);
    assert.equal(calls.filter(u => u === 'svg/add/CD.json').length, 1);
    assert.equal(calls.filter(u => u === 'svg/AB.json').length, 1, 'main chunks are cached');
  }));

const openPanel = (ex, expr) => ex.window.eval(`GRAPH = ${expr}; selectedNode = GRAPH.nodes[0]; showPanel(selectedNode)`);

test('a compound lists every species that reports it, most relevant first, with reference counts', () =>
  withExplorer({}, async ex => {
    const ik = 'REFJWTPEDVJJIY-UHFFFAOYSA-N'; // quercetin
    const n = ex.get(`D.ci['${ik}'].n_sp`);
    assert.ok(n > 300);
    ex.window.navToCompound(ik);
    const rows = [...ex.document.querySelectorAll('#panel .sp-section div[style*="max-height:220px"] > div')];
    assert.equal(rows.length, n, 'one row per species, not just 20 or 30');
    assert.match([...ex.document.querySelectorAll('#panel h3')].map(h => h.textContent).join('|'), new RegExp(`\\(${n}\\)`));
    const ing = rows.map(r => ex.get(`D.sp_ing_n[${JSON.stringify(r.querySelector('span').textContent)}] || 0`));
    assert.deepEqual(ing.slice(0, 40), [...ing.slice(0, 40)].sort((a, b) => b - a), 'species with more ingredients come first');
    for (const r of rows.slice(0, 20)) assert.match(r.querySelector('.sp-refs').textContent, /^\d+$/);
    assert.match(ex.document.querySelector('#panel .sp-note:not(.role-note)').textContent, new RegExp(`${n} 個物種報告過此化合物，其中 \\d+ 個只有 1 篇`));
    await sleep(200);
  }));

test('the graph of a compound reaches species beyond the first alphabetical ones', () =>
  withExplorer({}, async ex => {
    ex.window.navToCompound('REFJWTPEDVJJIY-UHFFFAOYSA-N');
    const species = ex.get(`GRAPH.nodes.filter(n => n.type === 'species').map(n => n.label)`);
    assert.equal(species.length, 20);
    assert.ok(species.some(sp => sp > 'Cu'), 'not only the first alphabetical species');
    await sleep(200);
  }));

test('a species without LOTUS data says so instead of showing nothing', () =>
  withExplorer({}, async ex => {
    const sp = ex.get(`Object.values(D.items).find(i => i.sp && !D.sc.shared[i.sp] && !D.sc.own_n[i.sp]).sp`);
    openPanel(ex, `buildEgoGraph('species', ${JSON.stringify(sp)})`);
    assert.match(ex.document.getElementById('panel').textContent, /LOTUS 沒有此物種的化合物資料.*不代表它不含化合物/);
    assert.equal(ex.document.querySelectorAll('#panel .sp-chem-card').length, 0);
    ex.window.setLang('en');
    assert.match(ex.document.getElementById('panel').textContent, /no phytochemistry has been published/);
    await sleep(100);
  }));

test('a species with compounds names LOTUS as the source, and says which other names were used', () =>
  withExplorer({}, async ex => {
    openPanel(ex, `buildEgoGraph('species', 'Lathyrus oleraceus')`);
    const notes = [...ex.document.querySelectorAll('#panel .sp-note')].map(n => n.textContent);
    assert.ok(notes.some(t => t.includes('Pisum sativum') && t.includes('GBIF')), 'synonym note');
    assert.ok(notes.some(t => t.includes('LOTUS ↗')), 'source note');
    assert.ok(ex.document.querySelector('#panel a[href="https://lotus.naturalproducts.net/"]'));
    openPanel(ex, `buildEgoGraph('species', 'Vitis vinifera')`);
    assert.ok(![...ex.document.querySelectorAll('#panel .sp-note')].some(n => n.textContent.includes('以其他學名記載')) || ex.get(`!!D.sc.via['Vitis vinifera']`));
    await sleep(200);
  }));

test('stereoisomers of one structure point at each other', () =>
  withExplorer({}, async ex => {
    const group = ex.get(`Object.values(D.planar).find(g => g.length >= 3)`);
    const [first, ...rest] = group;
    ex.window.navToCompound(first);
    const sec = [...ex.document.querySelectorAll('#panel .sp-section')].find(s => s.querySelector('h3')?.textContent.startsWith('同一平面結構'));
    assert.ok(sec, 'section present');
    assert.match(sec.querySelector('h3').textContent, new RegExp(`\\(${rest.length}\\)`));
    const row = sec.querySelector('.sib-row');
    row.click();
    assert.ok(rest.includes(ex.get('GRAPH.centerIdx')), 'clicking a row opens that stereoisomer');
    await sleep(200);
  }));

test('a species-specific compound shows how many references report it', () =>
  withExplorer({}, async ex => {
    ex.window.eval(`GRAPH = buildEgoGraph('species', 'Drimia maritima'); selectedNode = GRAPH.nodes[0]; showPanel(selectedNode)`);
    ex.document.getElementById('own-btn').click();
    await sleep(300);
    ex.document.querySelector('#own-grid .sp-chem-card').click();
    assert.match(ex.document.querySelector('#panel .sp-refs').textContent, /^\d+$/);
    await sleep(300);
  }));

test('a compound panel lists its chemical roles, the CosIng functions they suggest, and credits ChEBI', () =>
  withExplorer({}, async ex => {
    ex.window.navToCompound(QUERCETIN);
    const panel = ex.document.getElementById('panel');
    const chips = [...panel.querySelectorAll('.role-chip')].map(c => c.textContent);
    assert.equal(chips.length, ex.get(`D.ci['${QUERCETIN}'].cr.length`), 'one chip per role');
    assert.ok(chips.includes('plant metabolite') && chips.includes('antioxidant'));
    assert.ok(panel.querySelector('.role-more'), 'long lists fold the rest away');
    assert.equal(panel.querySelectorAll('.role-chips')[0].querySelectorAll('.role-chip').length, 10);
    assert.ok(panel.querySelector('.role-chip').title.length > 10, 'the chip carries the ChEBI definition');
    assert.ok(panel.querySelector('.role-fn'), 'roles that map to a function are marked');
    const section = [...panel.querySelectorAll('.sp-section')].find(sec => sec.querySelector('h3')?.textContent.startsWith('化學角色'));
    assert.ok(section);
    const fns = [...section.querySelectorAll('.sp-fn:not(.role-chip)')].map(f => f.textContent);
    assert.deepEqual(fns, ['ANTIOXIDANT', 'ANTIMICROBIAL', 'CHELATING']);
    assert.match(section.textContent, /ChEBI \d+（CC BY 4\.0）/);
    assert.ok(section.querySelector('a[href="https://www.ebi.ac.uk/chebi/"]'));
    section.querySelector('.sp-fn:not(.role-chip)').click();
    assert.equal(ex.get('GRAPH.centerType'), 'function');
    ex.window.navToCompound(QUERCETIN);
    ex.window.setLang('ja');
    assert.match(ex.document.getElementById('panel').textContent, /化学的な役割.*CC BY 4\.0/s);
    ex.window.setLang('en');
    assert.match(ex.document.getElementById('panel').textContent, /Chemical roles.*CosIng functions suggested by the roles.*CC BY 4\.0/s);
    assert.ok(ex.document.querySelector('.site-footer a[href="https://www.ebi.ac.uk/chebi/"]'));
    await sleep(200);
  }));

test('a species-specific compound shows its roles too, and one without roles shows no section', () =>
  withExplorer({}, async ex => {
    openPanel(ex, `buildEgoGraph('species', 'Abelmoschus esculentus')`);
    await ex.window.eval(`loadOwn('Abelmoschus esculentus')`);
    const [withCr] = ex.get(`D.own['Abelmoschus esculentus'].filter(r => r[7].length).map(r => r[0])`);
    assert.ok(withCr, 'fixture species has a compound with roles');
    ex.window.navToCompound(withCr);
    assert.ok(ex.document.querySelectorAll('#panel .role-chip').length > 0);
    ex.window.navToCompound(CAFFEINE);
    const hasSection = id => [...ex.document.querySelectorAll('#panel h3')].some(h => h.textContent.startsWith('化學角色'));
    assert.equal(hasSection(), ex.get(`!!D.ci['${CAFFEINE}'].cr`));
    ex.window.eval(`delete D.ci['${QUERCETIN}'].cr`);
    ex.window.navToCompound(QUERCETIN);
    assert.equal(ex.document.querySelectorAll('#panel .role-chip').length, 0);
    await sleep(200);
  }));

test('the Explorer still opens compound panels when roles.json is unavailable', () =>
  withExplorer({}, async ex => {
    ex.window.eval('D.roles = null');
    ex.window.navToCompound(QUERCETIN);
    assert.equal(ex.document.querySelectorAll('#panel .role-chip').length, 0);
    assert.match(ex.document.getElementById('panel').textContent, /quercetin/);
    await sleep(100);
  }));
