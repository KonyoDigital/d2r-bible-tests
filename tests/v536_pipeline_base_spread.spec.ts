import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v536 — PIPELINE base-spread. Konyo uploaded a Thresher AND a Cryptic Axe (both 5os merc polearms) plus the
// runes for two 5os merc words (Obedience + Honor). The Forge piled BOTH words onto the Thresher and left the
// Cryptic Axe idle — because the make-now bucket had a base-allocation pass (_nowCands + baseUsed) but the
// pipeline (Larzuk) bucket did not. This locks the fix: two makeable pipeline words → two DISTINCT owned bases.

test('two 5os merc words + two owned 5os Larzuk bases → each word gets its OWN base (no double-booking)', async ({ page }) => {
  await page.addInitScript(() => {
    // Obedience = Hel+Ko+Thul+Eth+Fal ; Honor = Amn+El+Ith+Tir+Sol (both cheap → pass the v576 endgame gate)
    localStorage.setItem('d2r_owned', JSON.stringify(['Thresher (Larzuk base)', 'Cryptic Axe (Larzuk base)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Amn: 2, Sol: 2, El: 1, Ith: 1, Tir: 1, Hel: 1, Ko: 1, Thul: 1, Eth: 1, Fal: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    ['Thresher (Larzuk base)', 'Cryptic Axe (Larzuk base)'].forEach((o) => { try { w._ensureSocketBaseEntry(o); } catch (e) {} });
    const s = w.forgeScan();
    const pipe = s.pipeline.filter((t: any) => t.rw === 'Obedience' || t.rw === 'Honor')
      .map((t: any) => ({ rw: t.rw, base: t.base && t.base.base }));
    const bases = pipe.map((p: any) => p.base);
    return { pipe, distinct: new Set(bases).size, count: pipe.length };
  });
  expect(r.count).toBe(2);                          // both words are pipeline tasks
  expect(r.distinct).toBe(2);                       // …on TWO DIFFERENT bases (not both on Thresher)
});

test('own 3× Thresher + 1 Cryptic Axe + two 5os words → uses DISTINCT base types (Thresher + Cryptic Axe), not two Threshers', async ({ page }) => {
  // Konyo's real case: d2r_copies says he owns 3 Threshers. Both 5os words COULD both sit on Threshers (he has
  // 3), but that reads as "Larzuk your Thresher ×2" and leaves the Cryptic Axe idle. v536.1 prefers a fresh base
  // TYPE before burning a 2nd copy → Thresher + Cryptic Axe, one clear card each.
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Thresher (Larzuk base)', 'Cryptic Axe (Larzuk base)']));
    localStorage.setItem('d2r_copies', JSON.stringify({ 'Thresher (Larzuk base)': 3 }));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Amn: 2, Sol: 2, El: 1, Ith: 1, Tir: 1, Hel: 1, Ko: 1, Thul: 1, Eth: 1, Fal: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    ['Thresher (Larzuk base)', 'Cryptic Axe (Larzuk base)'].forEach((o) => { try { w._ensureSocketBaseEntry(o); } catch (e) {} });
    const s = w.forgeScan();
    const bases = s.pipeline.filter((t: any) => t.rw === 'Obedience' || t.rw === 'Honor').map((t: any) => t.base && t.base.base);
    return { bases: bases.sort(), distinct: new Set(bases).size };
  });
  expect(r.distinct).toBe(2);                       // two distinct base TYPES despite owning 3 Threshers
  expect(r.bases).toContain('Cryptic Axe');         // the Cryptic Axe is used, not a 2nd Thresher
});

test('one 5os base + two 5os words → they group on the single base (fallback preserved, no phantom 2nd base)', async ({ page }) => {
  // Only a Thresher owned: both words must share it (you can only make one at a time). Spread must NOT invent a base.
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Thresher (Larzuk base)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Amn: 2, Sol: 2, El: 1, Ith: 1, Tir: 1, Hel: 1, Ko: 1, Thul: 1, Eth: 1, Fal: 1 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_rwProfile', 'fresh');   // v578.1 — Insight/Wind joined the seed; specs pin a fresh Chronicle
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Thresher (Larzuk base)');
    const s = w.forgeScan();
    const bases = s.pipeline.filter((t: any) => t.rw === 'Obedience' || t.rw === 'Honor').map((t: any) => t.base && t.base.base);
    return { bases };
  });
  // both fall back to the only owned base — every assigned base really is the Thresher
  expect(r.bases.length).toBeGreaterThan(0);
  expect(r.bases.every((b: string) => b === 'Thresher')).toBe(true);
});
