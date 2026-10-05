import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readData } from './helpers.mjs';

const ing = readData('ingredients.json');
const cpd = readData('compounds.json');
const ingCpd = readData('ingredient_compounds.json');
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
  for (const [ik, c] of Object.entries(cpd)) {
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
