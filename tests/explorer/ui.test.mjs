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
