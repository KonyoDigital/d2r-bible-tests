import { test, expect } from '@playwright/test';

// v350 — all off-grail base/exceptional/elite uniques are registered in EXTRA_ITEMS so the vault
// MATCHES them (no more throw-out), renders them in the in-game unique gold colour, with real-stat
// descriptions and base-type art (interim) until per-item HD art is added.

const URL = 'file://' + process.cwd() + '/bible.html';

test('off-grail uniques: matched, unique-coloured, art-backed, real stats', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.goto(URL);
  await page.waitForTimeout(2200);
  const r = await page.evaluate(() => {
    const w = window as any;
    const E = eval('EXTRA_ITEMS');
    // intake vocab (same build as the vault intake)
    let vocab = eval('ITEMS').map((i: any) => i.n).filter((n: string) => !/\((any piece|any|set)\)\s*$/i.test(n));
    try { if (w.__setPieceNames) vocab = Array.from(new Set(vocab.concat(w.__setPieceNames()))); } catch (e) {}
    vocab = Array.from(new Set(vocab.concat(Object.keys(E))));
    const vset = new Set(vocab);
    const offgrail = Object.keys(E).filter((n) => E[n].cat === 'Off-grail unique');
    const withArt = offgrail.filter((n) => !!(w.artUrl && w.artUrl(n)));
    return {
      count: offgrail.length,
      fechmarMatched: vset.has('Axe of Fechmar'),
      fechmarRarity: w._artRarity('Axe of Fechmar'),
      fechmarStats: (E['Axe of Fechmar'] || {}).stats || [],
      artCoverage: withArt.length,
    };
  });
  expect(errs).toEqual([]);
  expect(r.count).toBeGreaterThanOrEqual(100);   // ~107 off-grail uniques added
  expect(r.fechmarMatched).toBe(true);            // now in the intake vocab → no throw-out
  expect(r.fechmarRarity).toBe('unique');         // in-game gold colour
  expect(r.fechmarStats.join(' ')).toContain('Enhanced Damage');  // real game stats
  expect(r.artCoverage).toBeGreaterThan(r.count * 0.6);  // most have base-type art now
});
