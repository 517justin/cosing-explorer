import { test } from 'node:test';
import assert from 'node:assert/strict';
import { loadExplorer } from './helpers.mjs';

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
