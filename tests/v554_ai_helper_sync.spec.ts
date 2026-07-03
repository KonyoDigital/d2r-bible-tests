import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v554 — the AI Helper's snapshot is synced with the Forge: it now carries snapshot.forge (the owned-base-aware
// make-now / pipeline / one-step plan from forgeScan) + snapshot.chronicle (made/total), so "what should I make
// next" answers match the flagship instead of the older rune-only view.

test('buildAskSnapshot carries the Forge plan + Chronicle progress', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Colossus Voulge (4os)']));
    localStorage.setItem('d2r_runeStash', JSON.stringify({ Ral: 2, Tir: 2, Tal: 2, Sol: 2 }));
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  });
  await page.goto(URL); await page.waitForTimeout(1400);
  const r = await page.evaluate(() => {
    const w: any = window;
    w._ensureSocketBaseEntry('Colossus Voulge (4os)');
    const snap = w.buildAskSnapshot();
    return {
      hasForge: !!snap.forge,
      forgeKeys: snap.forge ? Object.keys(snap.forge) : [],
      makeNowIsArray: Array.isArray(snap.forge?.makeNow),
      hasChronicle: !!snap.chronicle,
      total: snap.chronicle?.total,
      madeIsNumber: typeof snap.chronicle?.made === 'number',
    };
  });
  expect(r.hasForge).toBe(true);
  expect(r.forgeKeys).toEqual(expect.arrayContaining(['makeNow', 'pipeline', 'oneStep']));
  expect(r.makeNowIsArray).toBe(true);
  expect(r.hasChronicle).toBe(true);
  expect(r.total).toBe(100);
  expect(r.madeIsNumber).toBe(true);
});
