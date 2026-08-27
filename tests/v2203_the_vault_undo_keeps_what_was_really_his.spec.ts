import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v2203 — UNDOING v2200, WHICH FILLED HIS VAULT FROM THE WRONG LEDGER.
//
// Konyo caught it: "im pretty sure the 400 items are all duplicates.. and also maybe READ CHRONICLE
// reads accidentally instead of inventory stash tooltip reads.. we said 41 items didnt we? so where
// did all this come from lol?"
//
// He was right. Two different facts, conflated by me:
//     d2r_foundLog   "the found-truth" (bible.html:3836) — everything ever FOUND. 392 entries.
//     d2r_owned      "physically in your stash" (bible.html:34625, its own words). Was FIVE.
// The real evidence for what is in his stash is tv/vault_seen.json: SEVENTEEN rows, one witness each.
//
// ⚠ v2200 COULD NOT UNDO ITSELF — it recorded only COUNTS, never the names it wrote. A migration
// that cannot name what it did cannot be reversed by its own record. The recovery came from a dated
// ledger snapshot instead (~/d2r_ledger_backups/ledger_2026-08-27_143930.json, owned = 5, taken
// before the v2200 boot at 16:08:48; the 16:09 snapshot reads 405). This undo records its names.
//
// THE THING THIS SPEC ACTUALLY PROTECTS: the undo must not be a blunt reset. Three populations live
// in d2r_owned and only ONE of them is the mistake.

const PRE = ['Waterwalk', "Cow King's Leathers (set)", 'Nagelring', 'Raven Frost',
             'Laying of Hands (bramble mitts)'];
const LIVE = ['Enigma', 'Goldwrap', 'Magefist'];

const SEED = `(function(){
  var R = window.ITEM_REGISTRY || {}, names = Object.keys(R);
  var isSet = function(n){ var i = R[n]; return i && i.tier === 'set'; };
  var uni = names.filter(function(n){ return !isSet(n); });
  var setp = names.filter(isSet);
  var fl = {}; uni.slice(0, 392).forEach(function(n){ fl[n] = '08/20/2026'; });
  var sp = setp.slice(0, 120);
  var PRE = ${JSON.stringify(PRE)}, LIVE = ${JSON.stringify(LIVE)};
  var owned = Object.keys(fl).concat(sp).concat(PRE).concat(LIVE);
  var tvx = {}; LIVE.forEach(function(n){ tvx[n] = { rarity:'basic', base:n, cat:'tv' }; });
  window.LSR.setItem('d2r_foundLog', JSON.stringify(fl));
  window.LSR.setItem('d2r_setPieces', JSON.stringify(sp));
  window.LSR.setItem('d2r_owned', JSON.stringify(owned));
  window.LSR.setItem('d2r_tvExtraItems', JSON.stringify(tvx));
  window.LSR.setItem('d2r_vaultBackfill_v2200', '{"fresh":423}');
  window.LSR.removeItem('d2r_vaultBackfillUndo_v2203');
  return owned.length;
})()`;

async function ready(page: any) {
  await page.waitForFunction(
    () => typeof (window as any).LSR !== 'undefined'
       && typeof (window as any).tvVaultRegister === 'function', null, { timeout: 120000 });
}

test('the undo drops only what came from found-ever, and keeps everything else', async ({ page }) => {
  await page.goto(URL);
  await ready(page);
  const before = await page.evaluate(SEED) as number;
  expect(before, 'the seeded vault is too small to reproduce his situation').toBeGreaterThan(400);

  await page.goto(URL);
  await ready(page);
  await page.waitForFunction(() => !!(window as any)._vaultBackfillUndo_v2203, null,
                             { timeout: 60000 });

  const r = await page.evaluate(() => {
    const own = JSON.parse((window as any).LSR.getItem('d2r_owned') || '[]') as string[];
    const uniq = new Set(own);
    return { n: own.length, distinct: uniq.size, list: [...uniq].sort(),
             report: (window as any)._vaultBackfillUndo_v2203 };
  });

  // ⚠ HIS FIVE. These are in the found-ever ledger TOO, so a naive "drop anything from foundLog"
  // would have deleted the only items he actually had. Recovered from the 14:39 snapshot.
  for (const n of PRE) {
    expect(r.list, `"${n}" was in his vault before v2200 ran and the undo deleted it. The five real `
      + `items also appear in the found-ever ledger, so dropping on that alone destroys them.`)
      .toContain(n);
  }
  // ⚠ AND ANYTHING THAT ARRIVED LEGITIMATELY SINCE. A TV DIABLO registration is stash evidence.
  for (const n of LIVE) {
    expect(r.list, `"${n}" was registered live by TV DIABLO — real stash evidence — and the undo `
      + `threw it away`).toContain(n);
  }
  expect(r.n, `the undo left ${r.n} items; only the ${PRE.length + LIVE.length} with an independent `
    + `claim should survive`).toBe(PRE.length + LIVE.length);

  // he suspected this outright: "im pretty sure the 400 items are all duplicates"
  expect(r.distinct, `d2r_owned carries ${r.n - r.distinct} duplicate row(s). It is a SET by `
    + `construction (the vault does owned.add(name)); genuine multiples live in d2r_copies.`)
    .toBe(r.n);
});

test('it runs once, and never on a machine where the backfill did not run', async ({ page }) => {
  await page.goto(URL);
  await ready(page);
  await page.evaluate(SEED);
  await page.goto(URL);                       // run 1
  await ready(page);
  await page.waitForFunction(() => !!(window as any)._vaultBackfillUndo_v2203, null,
                             { timeout: 60000 });
  const first = await page.evaluate(() =>
    JSON.parse((window as any).LSR.getItem('d2r_owned') || '[]').length);

  await page.goto(URL);                       // run 2 — must be inert
  await ready(page);
  await page.waitForTimeout(1200);
  const second = await page.evaluate(() => ({
    ran: !!(window as any)._vaultBackfillUndo_v2203,
    owned: JSON.parse((window as any).LSR.getItem('d2r_owned') || '[]').length,
  }));
  expect(second.ran, 'the undo ran a SECOND time — it is stamped for exactly this reason').toBe(false);
  expect(second.owned, 'the vault changed between boots after the undo settled').toBe(first);

  // a fresh machine — his cousin's — must never see it fire
  await page.evaluate(() => {
    const w = window as any;
    w.LSR.removeItem('d2r_vaultBackfill_v2200');
    w.LSR.removeItem('d2r_vaultBackfillUndo_v2203');
    w.LSR.setItem('d2r_owned', JSON.stringify(['Shako', 'Occulus']));
  });
  await page.goto(URL);
  await ready(page);
  await page.waitForTimeout(1200);
  const fresh = await page.evaluate(() => ({
    ran: !!(window as any)._vaultBackfillUndo_v2203,
    owned: JSON.parse((window as any).LSR.getItem('d2r_owned') || '[]'),
  }));
  expect(fresh.ran, 'the undo fired on a machine where the bad backfill never ran').toBe(false);
  expect(fresh.owned, 'it touched a vault it had no business touching').toEqual(['Shako', 'Occulus']);
});

test('the v2200 backfill is RETIRED, so a fresh machine is never filled wrongly', async ({ page }) => {
  await page.goto(URL);
  await ready(page);
  const out = await page.evaluate(() => {
    const w = window as any;
    // a clean machine with a real ledger — exactly the state that made his vault wrong
    w.LSR.setItem('d2r_foundLog', JSON.stringify({ Shako: '01/01/2026', Occulus: '01/01/2026' }));
    w.LSR.setItem('d2r_setPieces', JSON.stringify(["Tal Rasha's Adjudication"]));
    w.LSR.setItem('d2r_owned', JSON.stringify([]));
    w.LSR.removeItem('d2r_vaultBackfill_v2200');
    w.LSR.removeItem('d2r_vaultBackfillUndo_v2203');
    return true;
  });
  expect(out).toBe(true);
  await page.goto(URL);
  await ready(page);
  await page.waitForTimeout(1500);
  const after = await page.evaluate(() => ({
    owned: JSON.parse((window as any).LSR.getItem('d2r_owned') || '[]').length,
    flag: (window as any).LSR.getItem('d2r_vaultBackfill_v2200'),
  }));
  // THE WHOLE POINT: found-ever must never become physically-in-your-stash again
  expect(after.owned, 'the retired v2200 backfill still filled the vault from the found-ever '
    + 'ledger on a fresh machine — his cousin would get the same wrong vault he did').toBe(0);
  expect(after.flag, 'it did not stamp its flag, so it will be reconsidered on every load')
    .toBeTruthy();
});
