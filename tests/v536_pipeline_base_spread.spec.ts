import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v536 — PIPELINE base-spread. Konyo uploaded a Thresher AND a Cryptic Axe (both 5os merc polearms) plus the
// runes for two 5os merc words (Eternity + Honor). The Forge piled BOTH words onto the Thresher and left the
// Cryptic Axe idle — because the make-now bucket had a base-allocation pass (_nowCands + baseUsed) but the
// pipeline (Larzuk) bucket did not. This locks the fix: two makeable pipeline words → two DISTINCT owned bases.

test('two 5os merc words + two owned 5os Larzuk bases → each word gets its OWN base (no double-booking)', async ({ page }) => {
  await page.addInitScript(() => {
    // Eternity = Amn+Ber+Ist+Sol+Sur ; Honor = Amn+El+Ith+Tir+Sol
    localStorage.setItem('d2r_owned', JSON.stringify(['Thresher (Larzuk base)', 'Cryptic Axe (Larzuk base)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Amn: 2, Ber: 1, Ist: 1, Sol: 2, Sur: 1, El: 1, Ith: 1, Tir: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    ['Thresher (Larzuk base)', 'Cryptic Axe (Larzuk base)'].forEach((o) => { try { w._ensureSocketBaseEntry(o); } catch (e) {} });
    const s = w.forgeScan();
    const pipe = s.pipeline.filter((t: any) => t.rw === 'Eternity' || t.rw === 'Honor')
      .map((t: any) => ({ rw: t.rw, base: t.base && t.base.base }));
    const bases = pipe.map((p: any) => p.base);
    return { pipe, distinct: new Set(bases).size, count: pipe.length };
  });
  expect(r.count).toBe(2);                          // both words are pipeline tasks
  expect(r.distinct).toBe(2);                       // …on TWO DIFFERENT bases (not both on Thresher)
});

test('one 5os base + two 5os words → they group on the single base (fallback preserved, no phantom 2nd base)', async ({ page }) => {
  // Only a Thresher owned: both words must share it (you can only make one at a time). Spread must NOT invent a base.
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Thresher (Larzuk base)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Amn: 2, Ber: 1, Ist: 1, Sol: 2, Sur: 1, El: 1, Ith: 1, Tir: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Thresher (Larzuk base)');
    const s = w.forgeScan();
    const bases = s.pipeline.filter((t: any) => t.rw === 'Eternity' || t.rw === 'Honor').map((t: any) => t.base && t.base.base);
    return { bases };
  });
  // both fall back to the only owned base — every assigned base really is the Thresher
  expect(r.bases.length).toBeGreaterThan(0);
  expect(r.bases.every((b: string) => b === 'Thresher')).toBe(true);
});
