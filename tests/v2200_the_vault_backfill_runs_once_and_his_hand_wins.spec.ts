import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v2200 — THE VAULT HELD 5 ITEMS WHILE THE LEDGER HELD 512.
//
// Measured on his live board: d2r_foundLog 392 (a {name:date} MAP), d2r_setPieces 120 (an ARRAY of
// names), d2r_owned 5, d2r_muleAssign 4. The v2193 vault door routes at APPLY time, so it never ran
// over rows already in the ledger when it shipped.
//
// ⚠ THIS SPEC EXISTS FOR THE TWO THINGS THAT WOULD HAVE MADE THE FIX WORSE THAN THE BUG, both
// found by a fleet investigator reading the code rather than by running it:
//   1. renderVault is 7 functions / 16 innerHTML sites / 2 quadratic scans, and tvVaultRegister
//      calls it once per registration. 512 of them freeze his board at boot.
//   2. the v1954 wrapper logs one chronicle row per registration and _chLogUpsert CAPS THE LEDGER
//      AT 400 — 512 backfill rows would have evicted his entire chronicle history.
// Both are suppressed inside the migration. A test that only asserted "owned went up" would be
// green for a change that froze his board and ate his history. [[feedback-verify-not-proxy]]

const SEED = `(function(){
  var R = window.ITEM_REGISTRY || {};
  var names = Object.keys(R);
  var isSet = function(n){ var i = R[n]; return i && i.tier === 'set'; };
  var uni = names.filter(function(n){ return !isSet(n); });
  var setp = names.filter(isSet);
  var fl = {}; uni.slice(0, 392).forEach(function(n){ fl[n] = '08/20/2026'; });
  var sp = setp.slice(0, 120);            // ARRAY — the shape the board actually writes
  var own = uni.slice(0, 5);
  var asg = {}; own.slice(0, 4).forEach(function(n){ asg[n] = '__keep'; });
  window.LSR.setItem('d2r_foundLog', JSON.stringify(fl));
  window.LSR.setItem('d2r_setPieces', JSON.stringify(sp));
  window.LSR.setItem('d2r_owned', JSON.stringify(own));
  window.LSR.setItem('d2r_muleAssign', JSON.stringify(asg));
  window.LSR.removeItem('d2r_vaultBackfill_v2200');
  return { ledger: Object.keys(fl).length + sp.length, manual: own.slice(0, 4) };
})()`;

async function ready(page: any) {
  await page.waitForFunction(
    () => typeof (window as any).tvVaultRegister === 'function'
       && typeof (window as any).LSR !== 'undefined', null, { timeout: 120000 });
}

test('the backfill fills the vault, once, without freezing or evicting anything',
  async ({ page }) => {
    await page.goto(URL);
    await ready(page);

    const seed = await page.evaluate(SEED) as any;
    // the fixture must actually EXERCISE the gap, or every assertion below is vacuous
    expect(seed.ledger, 'the seeded ledger is too small to reproduce his situation')
      .toBeGreaterThan(400);
    expect(seed.manual.length, 'no manual placements were seeded, so "his hand wins" is untested')
      .toBe(4);

    // reload: the migration runs at boot, inside the vault IIFE, before the boot render
    await page.goto(URL);
    await ready(page);
    await page.waitForFunction(() => !!(window as any)._vaultBackfill_v2200, null, { timeout: 60000 });

    const r = await page.evaluate(() => {
      const w = window as any;
      const asg = JSON.parse(w.LSR.getItem('d2r_muleAssign') || '{}');
      return {
        report: w._vaultBackfill_v2200,
        owned: JSON.parse(w.LSR.getItem('d2r_owned') || '[]').length,
        assign: Object.keys(asg).length,
        assignMap: asg,
      };
    });

    expect(r.report.failed, `${r.report.failed} of ${r.report.names} registrations were refused`)
      .toBe(0);
    expect(r.owned, `the vault holds ${r.owned} items; the ledger held ${seed.ledger}`)
      .toBeGreaterThan(400);

    // ⚠ HIS HAND WINS. tvVaultRegister guards every assign write with !assign[name]; if that
    // guard is ever loosened, a migration silently re-files items he placed by hand.
    for (const n of seed.manual as string[]) {
      expect(r.assignMap[n], `the backfill overwrote his manual placement of "${n}" `
        + `(was __keep, now ${r.assignMap[n]}). A repair is a one-time event; a rule that `
        + `re-asserts itself over his judgement is a policy he did not ask for.`).toBe('__keep');
    }

    // ⚠ THE RENDER SUPPRESSION. 512 full renders freeze his board; the whole pass must be fast.
    expect(r.report.ms, `the backfill took ${r.report.ms}ms for ${r.report.names} names — the `
      + `renderVault suppression is not holding, and 512 full re-renders freeze his board at boot`)
      .toBeLessThan(5000);
  });

test('a second boot does not run it again', async ({ page }) => {
  await page.goto(URL);
  await ready(page);
  await page.evaluate(SEED);
  await page.goto(URL);                       // run 1
  await ready(page);
  await page.waitForFunction(() => !!(window as any)._vaultBackfill_v2200, null, { timeout: 60000 });
  const first = await page.evaluate(() => (window as any)._vaultBackfill_v2200.names);

  await page.goto(URL);                       // run 2 — must be a no-op
  await ready(page);
  const second = await page.evaluate(() => ({
    ran: !!(window as any)._vaultBackfill_v2200,
    flag: (window as any).LSR.getItem('d2r_vaultBackfill_v2200'),
    owned: JSON.parse((window as any).LSR.getItem('d2r_owned') || '[]').length,
  }));
  expect(first, 'the first run registered nothing, so re-running proves nothing').toBeGreaterThan(400);
  expect(second.ran, 'the migration ran a SECOND time — it is stamped for exactly this reason. '
    + 'v1816 next door: "a repair is a one-time event; a rule that re-asserts itself is a policy"')
    .toBe(false);
  expect(second.flag, 'the one-shot flag was not written, so it will run forever').toBeTruthy();
  expect(second.owned, 'the vault emptied between boots').toBeGreaterThan(400);
});

test('it refuses to fire on an empty ledger, and does not burn the flag doing it',
  async ({ page }) => {
    await page.goto(URL);
    await ready(page);
    await page.evaluate(() => {
      const w = window as any;
      w.LSR.setItem('d2r_foundLog', '{}');
      w.LSR.setItem('d2r_setPieces', '[]');
      w.LSR.removeItem('d2r_vaultBackfill_v2200');
    });
    await page.goto(URL);
    await ready(page);
    await page.waitForTimeout(1500);
    const out = await page.evaluate(() => ({
      ran: !!(window as any)._vaultBackfill_v2200,
      flag: (window as any).LSR.getItem('d2r_vaultBackfill_v2200'),
    }));
    // on a fresh install or a stranger's browser there is nothing to backfill; stamping "done"
    // there would silence the migration for the one person it exists for
    expect(out.ran, 'it ran on an empty ledger').toBe(false);
    expect(out.flag, 'it burned the one-shot flag without doing anything, so the real ledger '
      + 'would never be backfilled on this machine').toBeFalsy();
  });
