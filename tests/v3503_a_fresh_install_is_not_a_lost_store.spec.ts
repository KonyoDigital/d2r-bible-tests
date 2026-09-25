import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* REG-1275 (#165) — A FRESH INSTALL IS NOT A LOST STORE.

   The loss detector (v2988) calls an empty ledger a LOSS when a one-time key already exists, and promised "a fresh
   install is unaffected, by construction". The same boot writes those keys first, so the very first load of a brand
   new board recorded d2r_storeEmptied ("the store lost its contents") and the seed floor refused - on every later
   load too. MEASURED before the fix: fresh profile, first load found 0 + storeEmptied; second load the same. After:
   first load found 310, no loss on record. And a store that DID run and then emptied is still caught. */

async function boot(page: any, seed: Record<string, string> = {}) {
  await page.addInitScript((d: Record<string, string>) => {
    if (sessionStorage.getItem('__v3503Seeded')) return;
    sessionStorage.setItem('__v3503Seeded', '1');
    for (const k of Object.keys(d)) localStorage.setItem(k, d[k]);
  }, seed);
  await page.goto(URL);
  await page.waitForTimeout(2500);
  return page.evaluate(() => ({
    hadRun: (window as any).__d2rHadRunAtBoot,
    found: (window as any).funiScan().found,
    lossOnRecord: !!localStorage.getItem('d2r_storeEmptied'),
  }));
}

test('★ a brand-new board is floored on its FIRST load and nothing calls it a loss', async ({ page }) => {
  const r = await boot(page);
  expect(r.hadRun, 'a fresh install read its own first boot as history').toBe(false);
  expect(r.lossOnRecord, 'a fresh install was filed as a LOST store').toBe(false);
  expect(r.found, 'the seed floor refused a brand-new owner board').toBeGreaterThan(0);
  await page.reload();
  await page.waitForTimeout(2500);
  const again = await page.evaluate(() => !!localStorage.getItem('d2r_storeEmptied'));
  expect(again, 'the second load of a healthy board recorded a loss').toBe(false);
});

test('★ a store that RAN and then emptied is still caught, and the floor still refuses it', async ({ page }) => {
  const r = await boot(page, { d2r_pieceAlias_v2: '1', d2r_chronSyncMerged_v1: '1' });
  expect(r.hadRun, 'premise: this board had run before').toBe(true);
  expect(r.lossOnRecord, 'an emptied store went unrecorded - the v2988 loss is hidden again').toBe(true);
  expect(r.found, 'the floor papered over a real loss').toBe(0);
});
