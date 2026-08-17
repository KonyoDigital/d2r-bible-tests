// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';

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
    // v384 — HD art is now EITHER maxroll mr_*.png OR the true in-game CASC hd_*.png (the latter wins for
    // codename uniques like Pus Spitter/Skewer of Krintiz whose real sprite was extracted). Both count.
    const hdArt = offgrail.filter((n) => { const u = w.artUrl && w.artUrl(n); return u && /(mr_|hd_)/.test(u); });
    return {
      count: offgrail.length,
      fechmarMatched: vset.has('Axe of Fechmar'),
      fechmarRarity: w._artRarity('Axe of Fechmar'),
      fechmarStats: (E['Axe of Fechmar'] || {}).stats || [],
      fechmarArt: w.artUrl('Axe of Fechmar') || '',
      hdArtCoverage: hdArt.length,
    };
  });
  expect(errs).toEqual([]);
  // v369.3 — 5 entries (Gull, Harlequin Crest, The Cranium Basher, Crescent Moon, Hellfire Torch) were
  // REMOVED: they collided with existing grail items / the Hellfire Torch material card and hijacked
  // openDrop/navigateToItem routing (CI red). They still resolve via their grail "(base)" names. So the
  // off-grail count is now ~102, not 107 — thresholds lowered to ≥100 accordingly.
  expect(r.count).toBeGreaterThanOrEqual(100);   // ~102 off-grail uniques after removing 5 grail/material dupes
  expect(r.fechmarMatched).toBe(true);            // now in the intake vocab → no throw-out
  expect(r.fechmarRarity).toBe('unique');         // in-game gold colour
  expect(r.fechmarStats.join(' ')).toContain('Enhanced Damage');  // real game stats
  expect(r.fechmarArt).toContain('mr_axeoffechmar');   // HD per-item art (maxroll), self-hosted
  expect(r.hdArtCoverage).toBeGreaterThanOrEqual(100);  // (nearly) all have HD art now
});
