import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v564 — permanent locks from the full Tools/Forge audit (2026-07-04, the v552 open item):
//  A) every nav tab renders active with content and ZERO page/console errors;
//  B) every Tools card expands via its real header click, non-empty, error-free;
//  C) ONE-ENGINE PROPAGATION: ticking a word ✓ in the Chronicle moves the Chronicle count, Smart Insights
//     and the live loot filter TOGETHER (and untick restores) — the platform's core sync promise.

test('A — all nav tabs render active, with content, zero errors', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(URL); await page.waitForTimeout(1500);
  const tabs: string[] = await page.evaluate(() =>
    Array.from(document.querySelectorAll('.tab[data-tab]')).map((e) => e.getAttribute('data-tab')!));
  expect(tabs.length).toBeGreaterThanOrEqual(15);
  const results: any[] = [];
  for (const t of [...new Set(tabs)]) {
    await page.evaluate((t) => (window as any).switchTab(t), t);
    await page.waitForTimeout(300);
    results.push(await page.evaluate((t) => {
      const el = document.getElementById('tab-' + t);
      return { t, active: !!(el && el.classList.contains('active')), len: el ? el.textContent!.length : -1 };
    }, t));
  }
  for (const r of results) { expect(r.active).toBe(true); expect(r.len).toBeGreaterThan(500); }
  expect(errs).toEqual([]);
});

test('B — every Tools card expands via its real header click, non-empty, zero errors', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(URL); await page.waitForTimeout(1500);
  await page.evaluate(() => (window as any).switchTab('tools'));
  const cards: string[] = await page.evaluate(() =>
    Array.from(document.querySelectorAll('[id$="-card"]')).map((e) => e.id));
  expect(cards.length).toBeGreaterThanOrEqual(20);
  for (const id of [...new Set(cards)]) {
    await page.evaluate((id) => {
      const c = document.getElementById(id)!;
      const hdr = c.querySelector('.boss-header,[onclick*="toggleCardCollapse"]') as HTMLElement | null;
      if (hdr && c.classList.contains('collapsed')) hdr.click();
    }, id);
    await page.waitForTimeout(150);
    const len = await page.evaluate((id) => document.getElementById(id)!.innerHTML.length, id);
    expect(len, id + ' should render content').toBeGreaterThan(300);
  }
  expect(errs).toEqual([]);
});

test('C — Chronicle ✓ toggle propagates to Smart Insights + loot filter, and untick restores', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(async () => {
    const w: any = window;
    const madeCount = () => { const m = JSON.parse(localStorage.getItem('d2r_rwMade') || '{}');
      return Object.keys(w.RUNEWORD_TIP).filter((n: string) => m[n]).length; };
    const snap = () => ({ made: madeCount(), smart: w._smartProgress().made, filterBases: w._endgameFilterBases().codes.length });
    // pick a word that is currently UNMADE so the toggle direction is deterministic
    const m0 = JSON.parse(localStorage.getItem('d2r_rwMade') || '{}');
    const word = Object.keys(w.RUNEWORD_TIP).find((n: string) => !m0[n] && !(w._rwLadderBlocked && w._rwLadderBlocked(n)))!;
    const before = snap();
    w.rwToggleMade(word); await new Promise((res) => setTimeout(res, 150));
    const after = snap();
    w.rwToggleMade(word); await new Promise((res) => setTimeout(res, 150));
    const restored = snap();
    return { word, before, after, restored };
  });
  expect(r.after.made).toBe(r.before.made + 1);            // Chronicle moved
  expect(r.after.smart).toBe(r.before.smart + 1);          // Smart Insights moved with it
  expect(r.after.filterBases).toBeLessThanOrEqual(r.before.filterBases);  // filter never grows on a ✓
  expect(r.restored).toEqual(r.before);                    // untick restores every surface
});

// v584 — the aura gifs are the clean ANIMATED Amazon Basin set (the old imgur-hash gifs dissolved into
// rainbow static mid-animation — corrupt per-frame palettes). Every AURA_ART entry must resolve and load.
test('D — every AURA_ART entry points at a clean self-hosted gif that actually loads', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(async () => {
    const w: any = window;
    const entries = Object.entries(w.AURA_ART || {});
    const results: any[] = [];
    for (const [name, u] of entries) {
      const ok = await new Promise((res) => {
        const im = new Image();
        im.onload = () => res(im.naturalWidth > 0);
        im.onerror = () => res(false);
        im.src = String(u);
      });
      results.push({ name, u, ok, named: /aura_[a-z_]+\.gif$/.test(String(u)) });
    }
    return results;
  });
  expect(r.length).toBeGreaterThanOrEqual(11);
  for (const e of r) {
    expect(e.ok, e.name + ' gif loads (' + e.u + ')').toBe(true);
    expect(e.named, e.name + ' uses the clean named file').toBe(true);
  }
});
