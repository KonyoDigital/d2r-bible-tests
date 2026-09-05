import { test, expect } from './_net_stub';
import * as path from 'path';

// v2193 — THE VAULT COULD NEVER RECEIVE AN ITEM THE GRAIL ALREADY KNEW.
//
// Konyo: "all the reels were read okay.. so how come they weren't extracted data wise and counted
// for and then after verification of witnesses how come it didn't get routed to vault manager? we
// need to see vault manager flowing with traffic .. i want to see hundreds of items eventually
// auto arranged."
//
// MEASURED ON HIS OWN 84-KEY STORE, driving the REAL chronicleApply with his REAL 281 accepted
// names, before changing anything:
//
//     d2r_foundLog  390        d2r_owned  5        d2r_muleAssign  4
//     apply(281)  ->  uniques 0 · vaulted 4 · SKIPPED 279
//
// Two joints, both in the same function, both making "found" and "physically in my stash"
// mutually exclusive when they are two facts about ONE item:
//
//   1. `if (_chronAlreadyUni(n)) { res.skipped.push(n); return; }` — an item the grail already
//      knew returned before reaching the vault door at all. 279 of his 281.
//   2. `if (_landed) res.uniques.push(n); else { …vault… }` — the vault door lived in the ELSE, so
//      it only ever ran for names the board does NOT recognise. His 5 owned items are exactly
//      those unrecognised ones.
//
// His framing, and it is the right one: "this grail thing though.. we created and invented that
// word.. its just a data coding database informating and coding properly."
//
// AFTER, same store, same call: vaulted 281 · owned 287 · muleAssign 280, and after a REAL reload
// (the v1991 scar: the load-time rebuild used to empty d2r_owned) 283 owned / 280 mules / 280
// .vm-cell rendering, with d2r_foundLog still 390 — ★ never un-find holds.
//
// This spec uses a SYNTHETIC store, so it proves the LAW without shipping his ledger.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/** A board that already knows these names as FOUND — the case that used to skip the vault. */
/* ⚠⚠ v2667 — I FIXED ONE CALL SITE AND CALLED THE CLASS DONE. This file has FIVE bare
   chronicleApply calls; the v2666 fix added `loc` to exactly one of them. The other four sat in
   THIS FILE — not another module, the next function down — which is the sweep rule failing at the
   smallest possible radius.
   ⚠ THEY WERE CHECKED ONE BY ONE, NOT BLANKET-FIXED, because a sibling spec (v2083) passes plain
   strings ON PURPOSE and its missing `loc` IS the law it tests. Copying this fix across would
   have broken a correct test. Classified by what each ASSERTS:
     :125  ownedOfOurs + muledOfOurs — the vault gained            -> needs loc
     :217  a failed registration is carried out, not swallowed     -> needs loc (no door, no failure)
     :230  skipped AND vaulted.length === 1                        -> needs loc
     :257  the door was NOT called for an already-vaulted name     -> needs loc, see below
   ⚠⚠ :257 WAS PASSING VACUOUSLY AND IS THE WORST OF THE FOUR. With no `loc`, _mayVault is false
   and the vault door is never called FOR ANY REASON — so an assertion that it was not called
   REDUNDANTLY passed for the exact opposite of the reason it claims. It was green and proving
   nothing. [[feedback-blind-fixture-green-gate]]
   ⚠ The gate is v2388 (9b2b06e9 "a chronicle sighting proves he FOUND it, never that he HOLDS
   it"), not v2343 as the earlier write-up said — verified with git log -S 'var _mayVault'. */
const ALREADY_FOUND = ['Andariel’s Visage', 'Arm of King Leoric', 'Raven Frost',
                       'Nagelring', 'Waterwalk'];

async function boot(page: any, seed: Record<string, any>) {
  await page.addInitScript((s: any) => {
    try {
      if (localStorage.getItem('__simSeeded') === '1') return;
      localStorage.clear();
      for (const k of Object.keys(s)) localStorage.setItem(k, JSON.stringify(s[k]));
      localStorage.setItem('__simSeeded', '1');
    } catch (e) {}
  }, seed);
  await page.goto(URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);
}

/* ⚠ bible.html SEEDS a default found ledger on first load ("a bare d2r_rwMade holding 99 entries
   is exactly what the seed re-mints on any Mac"), so foundLog is ~358 here, not 5. The law is
   about THESE names, so every assertion is name-specific rather than a total. */
const read = (page: any, names: string[]) => page.evaluate((ns: string[]) => {
  const g = (k: string) => { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } };
  const owned = g('d2r_owned') || [];
  const mules = g('d2r_muleAssign') || {};
  const fl = g('d2r_foundLog') || {};
  const norm = (x: string) => String(x || '').toLowerCase().replace(/[’']/g, "'").trim();
  const ownedSet = new Set(owned.map(norm));
  const muleSet = new Set(Object.keys(mules).map(norm));
  const flSet = new Set(Object.keys(fl).map(norm));
  return {
    ownedOfOurs: ns.filter((n) => ownedSet.has(norm(n))).length,
    muledOfOurs: ns.filter((n) => muleSet.has(norm(n))).length,
    foundOfOurs: ns.filter((n) => flSet.has(norm(n))).length,
    foundTotal: Object.keys(fl).length,
    cells: document.querySelectorAll('.vm-cell').length,
  };
}, names);

test('an item the grail already knows still reaches the vault', async ({ page }) => {
  const found: Record<string, string> = {};
  ALREADY_FOUND.forEach((n) => { found[n] = '2026-08-01'; });
  await boot(page, { d2r_foundLog: found, d2r_owned: [], d2r_muleAssign: {} });

  const before = await read(page, ALREADY_FOUND);
  expect(before.foundOfOurs, 'these names are not in the found ledger, so the SKIP path this spec '
    + 'exists for is never reached and it proves nothing').toBe(ALREADY_FOUND.length);
  expect(before.ownedOfOurs, 'the fixture already has them vaulted').toBe(0);

  const res = await page.evaluate((names: string[]) => {
    // ⚠⚠ STALE ASSERTION, NOT A CODE REGRESSION — and the code is RIGHT. These rows carried only
    // a name. Since v2343 the vault door is gated on WHERE the item is:
    //     window._vaultMayClaim = function(loc){
    //       var t = String(loc == null ? '' : loc).toLowerCase().trim();
    //       return window._VAULT_LANES.indexOf(t) >= 0; };
    // With no `loc` the lane is '', indexOf returns -1, `_mayVault` is false for EVERY row, and
    // nothing can vault. That is exactly the failure: expected 5, received 0 — not 4, not 1, but
    // all of them, because the gate is per-row and every row was missing the same field.
    // This spec was written at v2193, ~150 versions before that gate existed.
    // ⚠ ADDING `loc` IS FAITHFUL, NOT A WORKAROUND. Real reader-produced rows carry it —
    // bible.html:19263 banks `loc: (row && row.loc) || null` — and the vault legitimately refuses
    // to claim an item whose location nobody recorded. 'stash' is a real lane in _VAULT_LANES
    // ['equipped','stash','cube','belt','mule','locker','tomb','tombs'] and is the lane his own
    // banked vault rows actually carry.
    // ⚠ The law under test is UNCHANGED: an item the grail already knows must still reach the
    // vault. The fixture now states where it is, which is a fact the real pipeline always has.
    const r = (window as any).chronicleApply({ wouldAdd: { uniques: names.map((n) => ({ name: n, loc: 'stash' })), sets: [] } });
    try { (window as any).vaultAutoAssign && (window as any).vaultAutoAssign(); } catch (e) {}
    return { skipped: (r && r.skipped || []).length, vaulted: (r && r.vaulted || []).length };
  }, ALREADY_FOUND);

  // the GRAIL tick is still skipped — ★ never un-find, and re-stamping a date he has is a lie
  expect(res.skipped, 'a name already in the grail was re-ticked').toBe(ALREADY_FOUND.length);

  const after = await read(page, ALREADY_FOUND);
  expect(after.ownedOfOurs, `the vault gained ${after.ownedOfOurs} of ${ALREADY_FOUND.length} items the reader `
    + `saw in his stash. Every one of them was already in the grail, and that used to return early `
    + `before the vault door — 279 of his 281 real items died on that line.`)
    .toBe(ALREADY_FOUND.length);
  expect(after.muledOfOurs, 'nothing was auto-arranged into a locker').toBe(ALREADY_FOUND.length);
  expect(after.foundTotal, 'the grail changed — the apply must never un-find or re-date')
    .toBe(before.foundTotal);
});

test('the vault survives a reload, which is where v1991 lost it', async ({ page }) => {
  const found: Record<string, string> = {};
  ALREADY_FOUND.forEach((n) => { found[n] = '2026-08-01'; });
  await boot(page, { d2r_foundLog: found, d2r_owned: [], d2r_muleAssign: {} });
  await page.evaluate((names: string[]) => {
    (window as any).chronicleApply({ wouldAdd: { uniques: names.map((n) => ({ name: n, loc: 'stash' })), sets: [] } });
    try { (window as any).vaultAutoAssign && (window as any).vaultAutoAssign(); } catch (e) {}
  }, ALREADY_FOUND);

  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(5000);
  const after = await read(page, ALREADY_FOUND);

  // v1991: "d2r_owned 0 <- every one gone, .vm-cell 0". Working and appearing to work are
  // separated by exactly this reload.
  expect(after.ownedOfOurs, 'the load-time rebuild emptied the vault again — the names were never '
    + 'made REAL via _tvExtraRemember, which is the v1991 defect').toBe(ALREADY_FOUND.length);
  expect(after.cells, 'the vault grid renders nothing after a reload').toBeGreaterThanOrEqual(
    ALREADY_FOUND.length);
});


// ── v2194 — THE BUTTON HE ACTUALLY PRESSES ────────────────────────────────────────────────────
// Konyo, looking at WAITING ON YOU: "is this ticking my chronicle count tally? or is it asking me
// to tally it in my vault manager? i would like it to show the distinguish the difference so i
// know and its clear so it can be a dual income notified and verifier for me and route it and
// funnel it accordingly."
//
// It ticked the CHRONICLE only and said nothing about it. And the same false split lived here a
// THIRD time: kaiChronicleAccept returns early when the chronicle has already settled the name —
// which is the most likely row for him to press — and that return came before the vault door.
// Measured in a real page: {already:true, store:'foundLog'} and d2r_owned did not move.

test('tick it records BOTH ledgers and names each one', async ({ page }) => {
  await boot(page, { d2r_owned: [], d2r_muleAssign: {} });
  const r = await page.evaluate(() => {
    const g = (k: string) => { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } };
    const before = (g('d2r_owned') || []).length;
    const res = (window as any).kaiChronicleAccept("Andariel's Visage");
    try { (window as any).vaultAutoAssign && (window as any).vaultAutoAssign(); } catch (e) {}
    return { res, before, after: (g('d2r_owned') || []).length,
             mules: Object.keys(g('d2r_muleAssign') || {}).length };
  });

  expect(r.res && r.res.ok, 'the accept failed outright').toBe(true);
  expect(r.after, `pressing "tick it" moved d2r_owned from ${r.before} to ${r.after}. It used to `
    + `tick the Chronicle ONLY and return before the vault door — and for a name the Chronicle `
    + `already knew it returned even earlier, which is most of his queue.`)
    .toBeGreaterThan(r.before);
  expect(r.mules, 'the item was vaulted but never given a locker').toBeGreaterThan(0);

  // ⚠ the DUAL REPORT: he must be able to tell which ledger moved, per press
  expect(r.res.chronicle, 'the result does not say what happened to the Chronicle').toBeTruthy();
  expect(r.res.vault, 'the result does not say what happened to the Vault').toBeTruthy();
  expect(String(r.res.say || '').toLowerCase(), 'the sentence does not name BOTH ledgers, so the '
    + 'surface cannot tell him where his item went').toContain('vault');
  expect(String(r.res.say || '').toLowerCase()).toContain('chronicle');
});

test('the button says where it sends the item, before he presses it', async ({ page }) => {
  const html = require('fs').readFileSync(
    require('path').resolve(__dirname, '..', 'bible.html'), 'utf8');
  /* v2674 — THE AMBIGUITY WAS FIXED BETTER THAN THIS TEST'S LETTER, so the letter had to move.
     The law is "the button says WHERE it sends the item, before he presses it". The old shape met
     it with ONE button labelled "tick it -> Chronicle + Vault"; the row now offers THREE separate
     destinations, which states it more plainly than a combined label ever did:
         .ibx-b.ibx-ok    _inboxAct('chronicle')   📖 Chronicle
         .ibx-b           _inboxAct('vault')       🏦 Vault
         .ibx-b.ibp-both  _inboxAct('accept')      📖🏦 Both
     Measured at HEAD: `tick it \u2192 Chronicle + Vault` appears 0 times, and the remaining "tick
     it" strings are prose and a search placeholder, not button labels — which is why the old count
     was 0 and read as a regression.
     ⚠ STILL BOTH RENDERERS, which is what "≥ 2" was protecting: the panel (`ibx-`) and the popover
     (`ibp-`) must EACH offer a named destination, or one door stays ambiguous. */
  const namedOk = (html.match(/class="ib[xp]-b [^"]*ib[xp]-ok"/g) || []).length;
  const namedBoth = (html.match(/class="ib[xp]-b [^"]*ibp-both"/g) || []).length;
  expect(namedOk, 'an inbox renderer offers no button that names the Chronicle as its destination')
    .toBeGreaterThanOrEqual(2);
  expect(namedBoth, 'an inbox renderer offers no button that names BOTH ledgers as its destination, '
    + 'so a row there cannot say whether it counts, files, or does both').toBeGreaterThanOrEqual(2);
  expect(html, 'a bare "tick it" button is the exact ambiguity he hit — it says nothing about where '
    + 'the item goes').not.toMatch(/>\s*tick it\s*</);
});


// ── v2195 — WHAT A CROSS-FAMILY REVIEW FOUND IN THE ARC, AND WHY EACH ONE MATTERS ─────────────

test('a vault write that FAILED never reports success', async ({ page }) => {
  /* ⚠ THE ELSE FIRED FOR BOTH 'already' AND 'no', so a registration that failed — or never ran,
     because the door was absent or threw into an empty catch — told him "the Vault already had it
     too". A failure wearing a success's words is the one thing a verifier must never do. */
  await boot(page, { d2r_owned: [], d2r_muleAssign: {} });
  const r = await page.evaluate(() => {
    (window as any).tvVaultRegister = () => ({ ok: false, why: 'the locker is full' });
    const a = (window as any).kaiChronicleAccept("Andariel's Visage");
    (window as any).tvVaultRegister = () => { throw new Error('door jammed'); };
    const b = (window as any).kaiChronicleAccept('Raven Frost');
    return { a, b };
  });
  for (const [label, res] of [['a refusal', r.a], ['a throw', r.b]] as any[]) {
    expect(String(res.say || '').toLowerCase(), `${label} was reported as a success: ${res.say}`)
      .toContain('refused');
    expect(res.vault, `${label} did not mark the vault as failed`).not.toBe('filed');
  }
});

test('a failed registration mid-sweep is CARRIED OUT, not swallowed', async ({ page }) => {
  /* Over hundreds of names a silent failure is a half-filled vault reported as a clean run.
     Earlier names are already written and nothing is rolled back, so the receipt must name what
     did not land. */
  await boot(page, { d2r_foundLog: { 'Raven Frost': '2026-08-01' }, d2r_owned: [], d2r_muleAssign: {} });
  const res = await page.evaluate(() => {
    (window as any).tvVaultRegister = () => ({ ok: false, why: 'quota exceeded' });
    return (window as any).chronicleApply({ wouldAdd: { uniques: [{ name: 'Raven Frost', loc: 'stash' }], sets: [] } });
  });
  expect(res.vaultFailed && res.vaultFailed.length, 'a registration failure vanished — the sweep '
    + 'reports a clean run over a vault that did not take the item').toBeGreaterThan(0);
  expect(String(res.vaultFailed[0].why)).toContain('quota');
});

test('the receipt names the overlap instead of leaving two ledgers to be subtracted', async ({ page }) => {
  /* `skipped` means the GRAIL did not move (★ never un-find). `vaulted` means the VAULT gained it.
     The names this arc exists for are BOTH at once, so the receipt says so rather than letting a
     reader infer it from counters that measure different ledgers. */
  await boot(page, { d2r_foundLog: { 'Raven Frost': '2026-08-01' }, d2r_owned: [], d2r_muleAssign: {} });
  const res = await page.evaluate(() =>
    (window as any).chronicleApply({ wouldAdd: { uniques: [{ name: 'Raven Frost', loc: 'stash' }], sets: [] } }));
  expect(res.skipped.length, 'the grail was re-ticked for a name it already had').toBe(1);
  expect((res.vaulted || []).length, 'the vault did not gain the item').toBe(1);
  expect(res.skippedButVaulted, 'the receipt does not name the overlap, so "skipped 279" reads as '
    + '"279 did nothing" when in fact all 279 were newly filed in the vault').toBe(1);
});

test('a no-op registration does not rewrite the store', async ({ page }) => {
  /* tvVaultRegister costs a dictionary write even in mode "already", and this runs once per name
     over hundreds. The in-memory check turns the common case into a lookup — and shrinks the
     window where a quota failure can stop the loop half-way. */
  /* ⚠ SEEDING d2r_owned DOES NOT SURVIVE THE PAGE. The load-time accept-list REBUILDS `owned`
     from the catalogues — measured: a seeded ['Raven Frost'] came back as 12 completely different
     names. That is the same rebuild v1991 fought, and it silently destroyed this test's premise:
     the name was not in the vault when the assertion ran, so the door was correctly called and I
     was measuring my own fixture. Use a name the rebuild KEEPS. [[feedback-suspect-the-instrument]] */
  /* ⚠⚠ v2689 — SEED THE STORE THE PRUNE ACTUALLY CONSULTS. The comment above chose a name the
     rebuild keeps; the real problem is which STORE vouches for it. bible.html's load-time prune
     drops any name that came ONLY from the found ledger — `if (fromLedger[c]) { dropped.push(n) }`
     — because d2r_owned is the PHYSICAL vault and d2r_foundLog is found-truth; a v677 tick writes
     the ledger only. So a foundLog-only seed is deliberately pruned and this test then measured an
     empty world, exactly the trap its own comment warns about one paragraph up.
     The prune KEEPS a name that is `_mine`, read straight from d2r_muleAssign (bible.html:39427).
     Filing Fleshrender to a mule is also what "the already-vaulted path" MEANS, so the fixture now
     matches the sentence in this test's own name instead of contradicting it. */
  await boot(page, {
    d2r_owned: ['Fleshrender'],
    d2r_foundLog: { Fleshrender: '2026-08-01' },
    d2r_muleAssign: { Fleshrender: 'M1' },
  });
  const seeded = await page.evaluate(() => {
    const g = (k: string) => { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } };
    return (g('d2r_owned') || []).indexOf('Fleshrender') >= 0;
  });
  expect(seeded, 'Fleshrender is not in the rebuilt vault, so this test is not exercising the '
    + 'already-vaulted path at all').toBe(true);
  const calls = await page.evaluate(() => {
    let n = 0;
    const real = (window as any).tvVaultRegister;
    (window as any).tvVaultRegister = function (x: any) { n++; return real.apply(this, arguments); };
    (window as any).chronicleApply({ wouldAdd: { uniques: [{ name: 'Fleshrender', loc: 'stash' }], sets: [] } });
    return n;
  });
  expect(calls, 'the vault door was called for a name already in the vault — hundreds of no-op '
    + 'dictionary writes per sweep').toBe(0);
});


test('the board never fetches when nothing is serving it', async ({ page }) => {
  /* ⚠ v2196 — CI CAUGHT A REGRESSION I SHIPPED. The v2189 tally POST fired unconditionally, and
     this page is also opened straight off disk — the end-to-end audit does exactly that — where a
     relative URL resolves to file:///api/board_tally and the fetch throws "URL scheme file is not
     supported". The .catch() swallows the REJECTION but the browser still logs a PAGE ERROR, and
     Routine G counts those: it went 8/8 to 7/8 on my own change.

     The console is what serves this page, so http(s) is exactly the condition under which a
     console exists to receive the POST. This spec runs from file://, which is the failing case. */
  const errors: string[] = [];
  page.on('pageerror', (e: any) => errors.push(String(e)));
  page.on('console', (m: any) => { if (m.type() === 'error') errors.push(m.text()); });
  await boot(page, { d2r_owned: [], d2r_muleAssign: {} });
  await page.evaluate(() => { try { (window as any).__tallyPersist(); } catch (e) {} });
  await page.waitForTimeout(1200);
  const tally = errors.filter((e) => /board_tally/i.test(e));
  expect(tally, `the board tried to POST from file:// and logged a page error: ${JSON.stringify(tally)}`)
    .toEqual([]);
});
