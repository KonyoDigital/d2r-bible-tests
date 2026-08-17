// v1754 — through the shared net stub: this spec asserts `expect(errors).toEqual([])`, and a
// console error array collects RESOURCE 404s as well as JS faults. bible.html pulls its
// typeface from fonts.googleapis.com, so on a runner with slow or blocked outbound network
// the spec goes red on the weather rather than on the code. The fixture fulfils fonts with an
// empty stylesheet (never aborts — an abort is itself a failed request).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v67 — Rune Stash & Cube-Up Planner (Runes tab). A pure round-trip of the user's own rune
// tally against the upgrade ratios ALREADY encoded in each RUNES[i].up recipe string
// ("3 El + ... → Eld" = 3:1, "2 Pul + ... → Um" = 2:1). Zero fabricated data: the ratio is
// parsed from the canonical recipe, RUNES is ordered ascending so cube-ups cascade by index.
// Counts persist to localStorage (d2r_runeStash) and ride along in the existing Backup/Share
// export. This spec locks the counter persistence, the cascade math, and the backup integration.
test.describe('v67 rune stash + cube-up planner', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.evaluate(() => { (window as any).uiConfirm = () => Promise.resolve(true); }).catch(() => {});
    await page.evaluate(() => { try { localStorage.removeItem('d2r_runeStash'); } catch (e) {} });
    await page.reload();
    await page.evaluate(() => { (window as any).uiConfirm = () => Promise.resolve(true); }).catch(() => {});
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(150);
  });

  test('renders a counter per rune, starts empty, and reflects the RUNES source', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cells = [...document.querySelectorAll('#rune-stash-grid .rune-stash-cell')];
      const names = cells.map((c) => c.getAttribute('data-rune'));
      const counts = cells.map((c) => (c.querySelector('.rs-count') as HTMLElement).textContent!.trim());
      return {
        cellCount: cells.length,
        runeLen: (RUNES as any[]).length,
        firstName: names[0],
        lastName: names[names.length - 1],
        allZero: counts.every((x) => x === '0'),
        fns: ['adjustRuneStash', 'cubeUpPotential', 'renderRuneStash', 'clearRuneStash'].map((n) => typeof (window as any)[n]),
      };
    });
    expect(r.cellCount).toBe(r.runeLen);        // one cell per rune, no drift from RUNES
    expect(r.firstName).toBe('El');             // ascending order preserved
    expect(r.lastName).toBe('Zod');
    expect(r.allZero).toBe(true);
    expect(r.fns.every((t) => t === 'function')).toBe(true);
  });

  test('adjusting a counter persists to localStorage and floors at zero', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).adjustRuneStash('El', 1);
      (window as any).adjustRuneStash('El', 1);
      (window as any).adjustRuneStash('El', 1);
      const afterPlus = JSON.parse(localStorage.getItem('d2r_runeStash') || '{}').El;
      const shownPlus = (document.querySelector('.rs-count[data-rune-count="El"]') as HTMLElement).textContent!.trim();
      // drive below zero — must clamp at 0 and drop the key, never go negative
      (window as any).adjustRuneStash('El', -1);
      (window as any).adjustRuneStash('El', -1);
      (window as any).adjustRuneStash('El', -1);
      (window as any).adjustRuneStash('El', -1);
      const afterMinus = JSON.parse(localStorage.getItem('d2r_runeStash') || '{}').El;
      const shownMinus = (document.querySelector('.rs-count[data-rune-count="El"]') as HTMLElement).textContent!.trim();
      return { afterPlus, shownPlus, afterMinus, shownMinus };
    });
    expect(r.afterPlus).toBe(3);
    expect(r.shownPlus).toBe('3');
    expect(r.afterMinus).toBeUndefined();   // key removed at zero (no negatives stored)
    expect(r.shownMinus).toBe('0');
  });

  test('cube-up cascade uses the exact in-game ratios (3:1 low/mid, 2:1 high/ultra)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const idxOf = (name: string) => (RUNES as any[]).findIndex((x) => x.n === name);
      // 9 El → 3 Eld → 1 Tir (two 3:1 steps), with 0 left toward a 4th rung
      for (let i = 0; i < 9; i++) (window as any).adjustRuneStash('El', 1);
      const eld = (window as any).cubeUpPotential(idxOf('Eld'));
      const tir = (window as any).cubeUpPotential(idxOf('Tir'));
      const nef = (window as any).cubeUpPotential(idxOf('Nef'));
      // a high-rune 2:1 step: 2 Pul → 1 Um
      (window as any).adjustRuneStash('Pul', 1);
      (window as any).adjustRuneStash('Pul', 1);
      const um = (window as any).cubeUpPotential(idxOf('Um'));
      // ratios read straight from the recipe strings
      const elRatio = (window as any).cubeUpPotential; // placeholder to keep tree-shake honest
      const ratios = {
        el: (RUNES as any[]).find((x) => x.n === 'El').up,
        pul: (RUNES as any[]).find((x) => x.n === 'Pul').up,
        zodUp: (RUNES as any[]).find((x) => x.n === 'Zod').up,
      };
      return { eld, tir, nef, um, ratios, hasFn: typeof elRatio };
    });
    expect(r.eld).toBe(3);     // 9 El / 3
    expect(r.tir).toBe(1);     // 3 Eld / 3
    expect(r.nef).toBe(0);     // nothing left to reach Nef
    expect(r.um).toBe(1);      // 2 Pul / 2
    expect(r.ratios.el).toMatch(/^3 El/);
    expect(r.ratios.pul).toMatch(/^2 Pul/);
    expect(r.ratios.zodUp).toBeNull();   // top of chain — no upgrade
  });

  test('the cube-up panel result tracks the selected target rune', async ({ page }) => {
    const r = await page.evaluate(() => {
      const idxOf = (name: string) => (RUNES as any[]).findIndex((x) => x.n === name);
      for (let i = 0; i < 9; i++) (window as any).adjustRuneStash('El', 1);
      const sel = document.getElementById('rune-cubeup-target') as HTMLSelectElement;
      sel.value = String(idxOf('Tir'));
      (window as any).renderRuneStash();
      const txt = (document.getElementById('cubeup-result') as HTMLElement).textContent!.replace(/\s+/g, ' ').trim();
      return { txt };
    });
    expect(r.txt).toBe('1× Tir');     // 9 El cascades to exactly 1 Tir
  });

  test('rune stash rides along in the Backup & Share export (round-trips with other state)', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).adjustRuneStash('Ist', 2);
      (window as any).exportProgress();
      const ta = document.getElementById('backup-textarea') as HTMLTextAreaElement;
      let ok = false, parsed: any = null;
      try { parsed = JSON.parse(ta.value); ok = true; } catch (e) {}
      const stash = ok ? JSON.parse(parsed.data['d2r_runeStash'] || '{}') : {};
      return { ok, hasKey: ok && 'd2r_runeStash' in parsed.data, ist: stash.Ist };
    });
    expect(r.ok).toBe(true);
    expect(r.hasKey).toBe(true);    // export snapshot carries the rune stash
    expect(r.ist).toBe(2);
  });

  test('no console errors across the rune-stash flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.evaluate(() => { (window as any).uiConfirm = () => Promise.resolve(true); }).catch(() => {});
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="tools"]');
    await page.waitForTimeout(150);
    await page.evaluate(() => {
      (window as any).adjustRuneStash('Vex', 3);
      (window as any).adjustRuneStash('Vex', -1);
      (window as any).renderRuneStash();
    });
    await page.waitForTimeout(120);
    expect(errors).toEqual([]);
  });
});
