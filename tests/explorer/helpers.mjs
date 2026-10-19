import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { JSDOM, VirtualConsole } from 'jsdom';

// COSING_DOCS lets the suite run against another build of the site.
const DOCS = process.env.COSING_DOCS
  ? pathToFileURL(path.resolve(process.env.COSING_DOCS) + path.sep)
  : new URL('../../docs/', import.meta.url);

export const docsUrl = rel => new URL(rel, DOCS);
export const readData = name => JSON.parse(fs.readFileSync(new URL(`data/${name}`, DOCS), 'utf8'));
export const sleep = ms => new Promise(r => setTimeout(r, ms));

// A canvas 2D context where every call is a no-op and returns itself.
const ctx = new Proxy(function () {}, {
  get: (_, k) => (k === 'width' ? 10 : ctx),
  apply: () => ctx,
  set: () => true,
});

/**
 * Load docs/index.html in jsdom with data files served from disk.
 * `query` is the URL query string ("?lang=ja"), `stored` seeds localStorage.lang.
 * Resolves once the page has finished loading its data. Call close() when done.
 */
export async function loadExplorer({ query = '', stored = null } = {}) {
  const html = fs.readFileSync(new URL('index.html', DOCS), 'utf8');
  const errors = [];
  const virtualConsole = new VirtualConsole();
  virtualConsole.on('jsdomError', e => errors.push(e.message));

  const dom = new JSDOM(html, {
    url: `http://localhost/${query}`,
    runScripts: 'dangerously',
    pretendToBeVisual: true,
    virtualConsole,
    beforeParse(window) {
      if (stored) window.localStorage.setItem('lang', stored);
      window.HTMLCanvasElement.prototype.getContext = () => ctx;
      window.matchMedia = () => ({ matches: false, addEventListener() {}, removeEventListener() {} });
      window.fetch = async url => {
        const u = String(url);
        if (/^https?:/.test(u) || u.startsWith('svg/')) return { ok: false, json: async () => ({}) };
        const text = fs.readFileSync(new URL(u, DOCS), 'utf8');
        return { ok: true, json: async () => JSON.parse(text), text: async () => text };
      };
    },
  });

  const { window } = dom;
  for (let i = 0; i < 100; i++) {
    if (window.eval('typeof D !== "undefined" && !!D && !!D.ci_by_sp')) break;
    await sleep(100);
  }
  if (!window.eval('typeof D !== "undefined" && !!D && !!D.ci_by_sp')) throw new Error('Explorer did not finish loading');

  return {
    window,
    document: window.document,
    errors,
    get: expr => structuredClone(window.eval(expr)),
    close: () => window.close(),
    async search(text) {
      const input = window.document.getElementById('search');
      input.value = text;
      input.dispatchEvent(new window.Event('input'));
      await sleep(300);
      return [...window.document.querySelectorAll('#sr .sr-item')].map(e => e.textContent.replace(/\s+/g, ' ').trim());
    },
  };
}
