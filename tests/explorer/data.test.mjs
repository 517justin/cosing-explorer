import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { readData } from './helpers.mjs';

const ing = readData('ingredients.json');
const cpd = readData('compounds.json');
const ingCpd = readData('ingredient_compounds.json');
const sc = readData('species_compounds.json');
const ownKey = sp => sp.slice(0, 2).toLowerCase().replace(/[^a-z]/g, '_');
const readOwn = key => JSON.parse(fs.readFileSync(new URL(`../../docs/own/${key}.json`, import.meta.url), 'utf8'));
const species = new Set(Object.values(ing.items).map(it => it.sp).filter(Boolean));

test('item indexes point at real functions and families', () => {
  for (const [ref, it] of Object.entries(ing.items)) {
    for (const f of it.f) assert.ok(f >= 0 && f < ing.functions.length, `${ref}: bad function index ${f}`);
    if (it.fm !== undefined) assert.ok(it.fm >= 0 && it.fm < ing.families.length, `${ref}: bad family index ${it.fm}`);
  }
  assert.equal(ing.order.length, Object.keys(ing.items).length);
});

test('functions and families are ordered by count, ties broken by name', () => {
  for (const [names, counts] of [[ing.functions, ing.fn_counts], [ing.families, ing.fam_counts]]) {
    for (let i = 1; i < names.length; i++) {
      assert.ok(
        counts[i - 1] > counts[i] || (counts[i - 1] === counts[i] && names[i - 1] < names[i]),
        `${names[i - 1]} (${counts[i - 1]}) before ${names[i]} (${counts[i]})`,
      );
    }
  }
});

test('common names only refer to known species and families', () => {
  const families = new Set(ing.families);
  for (const k of ['sp_zh', 'sp_en', 'sp_ja']) for (const sp of Object.keys(ing[k])) assert.ok(species.has(sp), `${k}: unknown species ${sp}`);
  for (const k of ['fam_zh', 'fam_en', 'fam_ja']) for (const f of Object.keys(ing[k])) assert.ok(families.has(f), `${k}: unknown family ${f}`);
});

test('no common name is blank or equal to the scientific name', () => {
  for (const k of ['sp_zh', 'sp_en', 'sp_ja', 'fam_zh', 'fam_en', 'fam_ja']) {
    for (const [sci, name] of Object.entries(ing[k])) {
      assert.ok(name.trim(), `${k}[${sci}] is blank`);
      assert.notEqual(name.toLowerCase(), sci.toLowerCase(), `${k}[${sci}] repeats the scientific name`);
    }
  }
});

test('compound names respect the per-language caps and contain no blanks', () => {
  const caps = { en: 3, zh: 4, ja: 5 };
  for (const [ik, c] of [...Object.entries(cpd), ...Object.entries(ingCpd)]) {
    for (const [lang, names] of Object.entries(c.nm || {})) {
      assert.ok(lang in caps, `${ik}: unexpected language ${lang}`);
      assert.ok(names.length >= 1 && names.length <= caps[lang], `${ik}.${lang}: ${names.length} names`);
      for (const n of names) assert.ok(n.trim(), `${ik}.${lang} has a blank name`);
    }
  }
});

test('descriptor arrays have nine values', () => {
  for (const [label, table] of [['compounds', cpd], ['ingredient_compounds', ingCpd]]) {
    for (const [ik, c] of Object.entries(table)) if (c.desc) assert.equal(c.desc.length, 9, `${label}.${ik}`);
  }
});

test('every ingredient structure resolves to exactly one compound record', () => {
  const overlap = Object.keys(ingCpd).filter(ik => ik in cpd);
  assert.deepEqual(overlap, [], 'ingredient_compounds.json must only hold compounds missing from compounds.json');
  const unresolved = Object.entries(ing.items).filter(([, it]) => it.ik && !(it.ik in cpd) && !(it.ik in ingCpd));
  assert.deepEqual(unresolved.map(([ref]) => ref), []);
});

test('compound species links stay within known species', () => {
  for (const [ik, c] of Object.entries(cpd)) {
    for (const [sp] of c.top_sp || []) assert.ok(species.has(sp), `${ik}: unknown species ${sp}`);
    assert.ok(c.n_sp >= 2, `${ik} has fewer than two species`);
  }
});

test('species_compounds.json lists every species of every shared compound, with no cap', () => {
  const keys = Object.keys(cpd);
  const seen = new Array(keys.length).fill(0);
  for (const [sp, idxs] of Object.entries(sc.shared)) {
    assert.ok(species.has(sp), `unknown species ${sp}`);
    assert.deepEqual(idxs, [...new Set(idxs)].sort((a, b) => a - b), `${sp}: indexes must be unique and ascending`);
    for (const i of idxs) {
      assert.ok(Number.isInteger(i) && i >= 0 && i < keys.length, `${sp}: bad compound index ${i}`);
      seen[i]++;
    }
  }
  const short = keys.filter((ik, i) => seen[i] !== cpd[ik].n_sp);
  assert.deepEqual(short, [], 'each compound must be listed under exactly n_sp species');
  for (const [i, ik] of keys.entries()) {
    for (const [sp] of cpd[ik].top_sp) assert.ok(sc.shared[sp].includes(i), `${ik}: top_sp ${sp} missing from the species list`);
  }
});

test('species-specific compounds: counts match the chunks and none is in compounds.json', () => {
  for (const [sp, n] of Object.entries(sc.own_n)) {
    const rows = readOwn(ownKey(sp))[sp];
    assert.equal(rows?.length, n, `${sp}: own_n says ${n}`);
    for (const [ik, formula, , , desc] of rows) {
      assert.ok(!(ik in cpd), `${ik} is shared, it must not be in an own chunk`);
      assert.equal(typeof formula, 'string');
      assert.ok(desc === null || desc.length === 9, `${ik}: bad descriptors`);
    }
  }
  const files = fs.readdirSync(new URL('../../docs/own/', import.meta.url)).map(f => f.replace('.json', ''));
  assert.deepEqual(files.sort(), [...new Set(Object.keys(sc.own_n).map(ownKey))].sort(), 'stale or missing chunk files');
});

test('an ingredient\'s compound count is its shared plus species-specific compounds', () => {
  for (const [ref, it] of Object.entries(ing.items)) {
    assert.ok(!('tc' in it), `${ref} still carries the retired tc preview`);
    if (!it.sp) continue;
    const total = (sc.shared[it.sp]?.length || 0) + (sc.own_n[it.sp] || 0);
    assert.equal(it.cc || 0, total, `${ref} (${it.sp})`);
  }
});
