import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v659 — GRAIL FOUND-SEED: the owner's in-game Chronicle (Unique tab, 56 screenshots 2026-07-12)
// seeded as a durable floor — 229 uniques owned + dated in d2r_foundLog on every boot, honoring
// explicit un-ticks (d2r_grailUnfound) and the fresh-profile flag. The F·Uniques universe gains
// the 62 mod-Chronicle uniques that live outside the calculator DB (_UNI_EXTRA) — F-tab only.

test('boot floors 229 found of the 364 F-Uniques universe, with exact in-game First Found stamps', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2000);
  const r = await page.evaluate(() => {
    const w: any = window;
    const s = w.funiScan();
    const fl = JSON.parse(localStorage.getItem('d2r_foundLog') || '{}');
    const owned = Object.keys(JSON.parse(localStorage.getItem('d2r_foundLog') || '{}'));   // v677 — the LEDGER is the found store; the vault stays physical
    return {
      total: s.total, found: s.found, flN: Object.keys(fl).length,
      seedN: Object.keys(w._GRAIL_SEED || {}).length, extraN: Object.keys(w._UNI_EXTRA || {}).length,
      wormskull: fl['Wormskull'],                       // matched ITEMS unique — exact in-game stamp
      hoz: owned.includes('Herald of Zakarum'),         // _UNI_EXTRA unique — owned + carded in the F-tab
      hozStamp: fl['Herald of Zakarum'],
      calcClean: (w.ITEMS || []).filter((x: any) => x.n === 'Herald of Zakarum').length,  // NEVER in the calculator DB
      vaultClean: JSON.parse(localStorage.getItem('d2r_owned') || '[]').length,           // v677 — the seed must NEVER touch the vault
    };
  });
  expect(r.seedN).toBe(243);   // v682 full reshoot: +13 gap finds (Djinn Slayer confirmed) · Nagelring real stamp
  // v1695 — THESE FOUR NUMBERS MOVED BECAUSE THE LEDGER GREW, WHICH IS THE WHOLE POINT OF THE ARC.
  // Konyo's instruction was explicit: "from 236 it NEEDS TO GO UP". Three genuine finds were read
  // off his own Chronicle screenshots and applied in v1693 -- Fleshrender (08/03 01:27 Diablo),
  // Gloom's Trap (07/27 01:29 Mephisto), The Diggler (Diablo). Every delta below is that +3, and
  // the numbers are only updated because each one is arithmetically accounted for:
  //   found 243 -> 246   (+3 finds)          flN 351 -> 354   (the same 3 reach the ledger)
  //   extraN 66 -> 67    (Fleshrender ONLY -- the other two already sit in the calculator DB)
  // ⚠ total is the one that is NOT explained by the finds: 368 -> 385 is the v1692 roster fix,
  // where the F-tally stopped looping a curated 83-item ITEMS list and counted the real roster.
  // 385 was independently verified at v1692 before this spec ever saw it.
  expect(r.extraN).toBe(67);   // v1695 +Fleshrender · v682 +Blackbog's Sharp/Radament's Sphere/Rakescar/Skull Collector
  expect(r.total).toBe(385);            // v1692 real-roster tally (was 368 = 302 calculator + 66 extras)
  expect(r.found).toBe(246);            // v1695: 243 + Fleshrender + Gloom's Trap + The Diggler
  expect(r.flN).toBe(354);   // v1695: 246 uniques + 108 set-piece stamps share the ledger
  expect(r.wormskull).toBe('Jun 22, 2026 · 02:00');
  expect(r.hoz).toBe(true);
  expect(r.hozStamp).toBeTruthy();
  expect(r.calcClean).toBe(0);          // extras stay OUT of ITEMS — the calculator/boss tables are untouched
  expect(r.vaultClean).toBe(0);         // v677 — zero chronicle names in the vault (Konyo throws finds away)
});

test('an explicit un-tick SURVIVES the floor (d2r_grailUnfound = user truth); re-tick clears it', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2000);
  await page.evaluate(() => (window as any).toggleOwned('Wormskull'));
  await page.reload(); await page.waitForTimeout(2000);
  const after = await page.evaluate(() => ({
    owned: !!JSON.parse(localStorage.getItem('d2r_foundLog') || '{}')['Wormskull'],   // v677
    gu: JSON.parse(localStorage.getItem('d2r_grailUnfound') || '{}')['Wormskull'],
    found: (window as any).funiScan().found,
  }));
  await page.evaluate(() => (window as any).toggleOwned('Wormskull'));
  await page.reload(); await page.waitForTimeout(2000);
  const restored = await page.evaluate(() => ({
    found: (window as any).funiScan().found,
    gu: JSON.parse(localStorage.getItem('d2r_grailUnfound') || '{}')['Wormskull'],
  }));
  await page.evaluate(() => { localStorage.removeItem('d2r_grailUnfound'); });
  // ⚠ THE CONTRACT THIS TEST EXISTS FOR IS UNCHANGED AND STILL PASSING: `owned` is false and the
  // un-tick is recorded. Only the COUNT moved, by the same +3 as the test above (246 - 1 = 245).
  // That distinction is the whole reason these numbers were updated rather than the code: if
  // `owned` or `gu` had moved, d2r_grailUnfound would have stopped being user truth and the fix
  // would belong in bible.html, not here.
  expect(after.owned).toBe(false);
  expect(after.gu).toBe(1);
  expect(after.found).toBe(245);        // v1695: 246 with Wormskull un-ticked
  expect(restored.found).toBe(246);     // v1695: 243 + the three v1693 finds
  expect(restored.gu).toBeUndefined();
});

test('fresh profile suppresses the grail floor entirely (a different player starts from zero)', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('d2r_rwProfile', 'fresh');
    localStorage.setItem('d2r_owned', JSON.stringify([]));
    localStorage.setItem('d2r_foundLog', JSON.stringify({}));
  });
  await page.goto(URL); await page.waitForTimeout(2000);
  const r = await page.evaluate(() => ({
    found: (window as any).funiScan().found,
    flN: Object.keys(JSON.parse(localStorage.getItem('d2r_foundLog') || '{}')).length,
  }));
  expect(r.found).toBe(0);
  expect(r.flN).toBe(0);
});
