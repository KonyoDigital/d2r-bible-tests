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
    const owned = JSON.parse(localStorage.getItem('d2r_owned') || '[]');
    return {
      total: s.total, found: s.found, flN: Object.keys(fl).length,
      seedN: Object.keys(w._GRAIL_SEED || {}).length, extraN: Object.keys(w._UNI_EXTRA || {}).length,
      wormskull: fl['Wormskull'],                       // matched ITEMS unique — exact in-game stamp
      hoz: owned.includes('Herald of Zakarum'),         // _UNI_EXTRA unique — owned + carded in the F-tab
      hozStamp: fl['Herald of Zakarum'],
      calcClean: (w.ITEMS || []).filter((x: any) => x.n === 'Herald of Zakarum').length,  // NEVER in the calculator DB
    };
  });
  expect(r.seedN).toBe(229);
  expect(r.extraN).toBe(62);
  expect(r.total).toBe(364);            // 302 calculator uniques + 62 chronicle extras
  expect(r.found).toBe(229);
  expect(r.flN).toBe(229);
  expect(r.wormskull).toBe('Jun 22, 2026 · 02:00');
  expect(r.hoz).toBe(true);
  expect(r.hozStamp).toBeTruthy();
  expect(r.calcClean).toBe(0);          // extras stay OUT of ITEMS — the calculator/boss tables are untouched
});

test('an explicit un-tick SURVIVES the floor (d2r_grailUnfound = user truth); re-tick clears it', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(2000);
  await page.evaluate(() => (window as any).toggleOwned('Wormskull'));
  await page.reload(); await page.waitForTimeout(2000);
  const after = await page.evaluate(() => ({
    owned: JSON.parse(localStorage.getItem('d2r_owned') || '[]').includes('Wormskull'),
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
  expect(after.owned).toBe(false);
  expect(after.gu).toBe(1);
  expect(after.found).toBe(228);
  expect(restored.found).toBe(229);
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
