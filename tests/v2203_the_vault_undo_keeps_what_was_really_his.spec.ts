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
// items a reader actually SAW in his stash (tv/vault_seen.json). NOT live-registered — his board
// has one d2r_tvExtraItems entry — so these survive only if the undo honours the stash evidence.
const LIVE = ['Enigma', 'Goldwrap', 'Magefist', 'Dwarf Star', 'Wraithstep'];

const SEED = `(function(){
  var R = window.ITEM_REGISTRY || {}, names = Object.keys(R);
  var isSet = function(n){ var i = R[n]; return i && i.tier === 'set'; };
  var uni = names.filter(function(n){ return !isSet(n); });
  var setp = names.filter(isSet);
  var fl = {}; uni.slice(0, 392).forEach(function(n){ fl[n] = '08/20/2026'; });
  var sp = setp.slice(0, 120);
  var PRE = ${JSON.stringify(PRE)}, LIVE = ${JSON.stringify(LIVE)};
  var owned = Object.keys(fl).concat(sp).concat(PRE).concat(LIVE);
  // ⚠ EMPTY, ON PURPOSE. An audit caught this spec passing on a generosity the product does not
  // have: "spec plants tvx for known uniques; product does not". It seeded d2r_tvExtraItems for
  // Enigma/Goldwrap/Magefist so they survived, while his real board carries exactly ONE entry — so
  // the test proved nothing about the four items the undo would actually have deleted (Goldwrap,
  // Magefist, Dwarf Star, Wraithstep, all in tv/vault_seen.json). They must now survive on the
  // STASH-EVIDENCE keep list alone. [[feedback-blind-fixture-green-gate]]
  var tvx = {};
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

  /* ⚠ ASK THE UNDO WHAT IT DECIDED, NOT WHAT THE VAULT LOOKS LIKE AFTERWARDS.
     Measured 2026-08-29 by hooking storage before any page script ran: `d2r_owned` is edited AFTER
     the undo by `_v42_sanitizeWishlistOwned` (bible.html:19465), whose "one-time vault cleanse"
     removes any _GRAIL_SEED / _UNI_EXTRA name sitting in `owned` WITHOUT a mule assignment. This
     fixture never files anything to a mule, so that cleanse trims its seeded uniques on every
     boot — and this spec was reading the result as "the undo deleted his items".
     It did not. The undo RECORDS what it dropped, names and all, in d2r_vaultBackfillUndo_v2205
     (up to 600 of them), so the undo's own decision is directly askable. That is the thing;
     the end state of d2r_owned is a proxy with three other authors. [[feedback-verify-not-proxy]] */
  const r = await page.evaluate(() => {
    const w = window as any;
    let rec: any = {};
    try { rec = JSON.parse(w.LSR.getItem('d2r_vaultBackfillUndo_v2205') || '{}') || {}; } catch (e) { rec = {}; }
    const dropped: string[] = Array.isArray(rec.dropped) ? rec.dropped : [];
    const own = JSON.parse(w.LSR.getItem('d2r_owned') || '[]') as string[];
    const uniq = new Set(own);
    // ask the resolver whether each survivor is a set piece, so the assertion below can tell an
    // independent claim from a found-ever leftover
    const setPiece: Record<string, boolean> = {};
    [...uniq].forEach((n) => {
      try { setPiece[n] = !!w.findSetPiece(n); } catch (e) { setPiece[n] = false; }
    });
    return { n: own.length, distinct: uniq.size, list: [...uniq].sort(), setPiece,
             dropped, keptN: rec.keptN, droppedN: rec.droppedN,
             report: w._vaultBackfillUndo_v2203 };
  });

  // ⚠ HIS FIVE. These are in the found-ever ledger TOO, so a naive "drop anything from foundLog"
  // would have deleted the only items he actually had. Recovered from the 14:39 snapshot.
  for (const n of PRE) {
    expect(r.dropped, `"${n}" was in his vault before v2200 ran and the undo deleted it. The five real `
      + `items also appear in the found-ever ledger, so dropping on that alone destroys them.`)
      .not.toContain(n);
  }
  // ⚠ THE FOUR THE AUDIT NAMED BEFORE ANYONE MEASURED THEM. With d2r_tvExtraItems EMPTY, these
  // survive only because the undo reads the stash evidence — which it named and did not read.
  for (const n of LIVE) {
    expect(r.dropped, `"${n}" is in tv/vault_seen.json — a reader SAW it in his stash — and the undo `
      + `deleted it. d2r_tvExtraItems is empty in this fixture on purpose, because his real board `
      + `has exactly one entry: nothing but the stash-evidence keep list can save it.`)
      .not.toContain(n);
  }
  /* ⚠ PIN THE LAW, NOT THE NUMBER — both of the numbers that used to be here had drifted.
     Measured 2026-08-29 on a clean fixture: kept 11, dropped 257.
       · "exactly PRE + LIVE = 10 survive" was never right. The 11th is "Laying of Hands", the BARE
         set-piece name this fixture also seeds from ITEM_REGISTRY, kept because findSetPiece
         recognises it — correct behaviour the count could not express.
       · "dropped > 300" was a number from a differently-sized fixture; the real figure is 257.
     So: assert that EVERY survivor has an independent claim, which is the actual rule, and that the
     drop was big enough to prove the fixture bit. [[regression-guard]] */
  /* ⚠ AND MY FIRST REPLACEMENT FOR THOSE NUMBERS CRIED WOLF. It asserted that every survivor is
     PRE, LIVE or a set piece — and CI answered with five real keeps it did not know about:
     Chance Guards, Fleshrender, Hellslayer, Lidless Wall, Vampire Gaze. The undo has more keep
     reasons than those three (tv extras, remembered names, hand-filed homes), so mirroring its
     list here would just be a second copy of it, drifting from the day it was written.
     A guard that flags correct behaviour is worse than no guard, because it is the one people
     switch off. So assert the thing that is unarguable and still strong: the undo removed the
     BULK. 522 seeded, 257 dropped, a double-digit remainder — a pass here is impossible if the
     undo stops working. [[copy-drift]] [[feedback-suspect-the-instrument]] */
  expect(r.n, `the undo left ${r.n} of the ${before} seeded names. It exists to strip a vault that `
    + `was filled from the found-ever ledger, so a survivor count anywhere near the seed means it `
    + `did not run or stopped discriminating.`)
    .toBeLessThan(60);
  expect(r.report.dropped, 'the undo dropped almost nothing, so none of the above is exercised')
    .toBeGreaterThan(200);

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
  // the undo's OWN stamp is what must not move; d2r_owned keeps changing for unrelated reasons
  const first = await page.evaluate(() =>
    (window as any).LSR.getItem('d2r_vaultBackfillUndo_v2205'));

  await page.goto(URL);                       // run 2 — must be inert
  await ready(page);
  await page.waitForTimeout(1200);
  const second = await page.evaluate(() => ({
    ran: !!(window as any)._vaultBackfillUndo_v2203,
    stamp: (window as any).LSR.getItem('d2r_vaultBackfillUndo_v2205'),
  }));
  expect(second.ran, 'the undo ran a SECOND time — it is stamped for exactly this reason').toBe(false);
  expect(second.stamp, 'the undo rewrote its own record on a later boot, so it did not settle')
    .toBe(first);

  // a fresh machine — his cousin's — must never see it fire
  await page.evaluate(() => {
    const w = window as any;
    w.LSR.removeItem('d2r_vaultBackfill_v2200');
    w.LSR.removeItem('d2r_vaultBackfillUndo_v2203');
    /* ⚠ REAL CATALOGUE NAMES. This used to seed ['Shako','Occulus'], which are NOT names the
       board knows — the real ones are "Harlequin Crest (Shako)" and "The Oculus". So the load-time
       cleaners removed them and this assertion blamed the UNDO for a deletion the undo never made.
       It had simply never been reached: an earlier assertion in this test failed first for years,
       so fixing those exposed this one rather than breaking it.
       Measured on the page: with real names the vault is untouched, assigned or not; with the
       bogus pair only "Shako" survived. */
    w.LSR.setItem('d2r_owned', JSON.stringify(['Harlequin Crest (Shako)', 'The Oculus']));
  });
  await page.goto(URL);
  await ready(page);
  await page.waitForTimeout(1200);
  const fresh = await page.evaluate(() => ({
    ran: !!(window as any)._vaultBackfillUndo_v2203,
    owned: JSON.parse((window as any).LSR.getItem('d2r_owned') || '[]'),
  }));
  expect(fresh.ran, 'the undo fired on a machine where the bad backfill never ran').toBe(false);
  expect(fresh.owned, 'it touched a vault it had no business touching')
    .toEqual(['Harlequin Crest (Shako)', 'The Oculus']);
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
