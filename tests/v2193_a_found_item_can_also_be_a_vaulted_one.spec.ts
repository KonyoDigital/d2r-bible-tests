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
    const r = (window as any).chronicleApply({ wouldAdd: { uniques: names.map((n) => ({ name: n })), sets: [] } });
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
    (window as any).chronicleApply({ wouldAdd: { uniques: names.map((n) => ({ name: n })), sets: [] } });
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
  // both inbox renderers must label it — a button that says only "tick it" is the ambiguity he hit
  const labelled = (html.match(/tick it \\u2192 Chronicle \+ Vault/g) || []).length;
  expect(labelled, 'an inbox row still offers a bare "tick it", which does not say whether it '
    + 'counts in the Chronicle, files in the Vault, or both').toBeGreaterThanOrEqual(2);
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
    return (window as any).chronicleApply({ wouldAdd: { uniques: [{ name: 'Raven Frost' }], sets: [] } });
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
    (window as any).chronicleApply({ wouldAdd: { uniques: [{ name: 'Raven Frost' }], sets: [] } }));
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
  await boot(page, { d2r_foundLog: { Fleshrender: '2026-08-01' }, d2r_muleAssign: {} });
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
    (window as any).chronicleApply({ wouldAdd: { uniques: [{ name: 'Fleshrender' }], sets: [] } });
    return n;
  });
  expect(calls, 'the vault door was called for a name already in the vault — hundreds of no-op '
    + 'dictionary writes per sweep').toBe(0);
});
