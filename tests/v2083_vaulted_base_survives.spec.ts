import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v2083 — A BASE APPLIED FROM A REEL HELD FOR ONE PAGE-LIFE, THEN VANISHED.
//
// v1987 refused a fix here and said exactly why: "chronicleApply reports `vaulted` for a base, yet
// d2r_owned does not gain it, so nothing reaches ownedPool() and nothing can be filed. That needs
// its own pass with the scope established first, not a guess at the end of an arc."
//
// MEASURED, a real apply then a reload:
//     apply Shako · Phase Blade · Monarch · Archon Plate
//       res.vaulted  all four      d2r_owned 4 ✓      muleAssign 0
//     ...reload
//       d2r_owned    0   <- every one gone            .vm-cell  0
//   and after the fix: owned 4, muleAssign 4, .vm-cell 4, .vm-grid 2.
//
// TWO joints: the name never became KNOWN (the load-time accept-list rebuilds `owned` from the
// catalogues and a base is in none of them), and it was never FILED.
//
// ⚠ THIS SPEC EXISTS BECAUSE A SOURCE GUARD CANNOT PROVE IT. Sabotaging the remember to
// `0 && window._tvExtraRemember(...)` leaves the searched text in the file, so the source
// assertion passes while the call is dead. Only a reload can tell.
//
// VENUE: a browser spec. Runs on GitHub CI, never on his Mac. [[test-venue]]

const BASES = ['Shako', 'Phase Blade', 'Monarch', 'Archon Plate'];

async function cleanWorld(page: any) {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  await page.evaluate(() => {
    const ks: string[] = [];
    for (let i = 0; i < localStorage.length; i++) ks.push(localStorage.key(i) as string);
    ks.forEach((k) => { if (/d2r_/.test(k)) localStorage.removeItem(k); });
  });
}

async function applyBases(page: any) {
  return page.evaluate((bases: string[]) => {
    const w: any = window;
    const res = w.chronicleApply({ wouldAdd: { uniques: bases, sets: [] } });
    try { w.vaultAutoAssign && w.vaultAutoAssign(); } catch (e) {}
    const P = w._D2R_PFX || '';
    return {
      vaulted: res.vaulted || [],
      owned: JSON.parse(localStorage.getItem(P + 'd2r_owned') || '[]').length,
      extras: Object.keys(JSON.parse(localStorage.getItem(P + 'd2r_tvExtraItems') || '{}')).length,
    };
  }, BASES);
}

test('the apply really vaults them, or nothing below means anything', async ({ page }) => {
  await cleanWorld(page);
  await page.goto(URL);
  await page.waitForTimeout(1800);
  const r = await applyBases(page);
  expect(r.vaulted.length, 'no base was vaulted — the fixture cannot demonstrate survival').toBe(BASES.length);
  expect(r.owned).toBe(BASES.length);
});

test('a vaulted base SURVIVES a reload and reaches a mule', async ({ page }) => {
  await cleanWorld(page);
  await page.goto(URL);
  await page.waitForTimeout(1800);
  await applyBases(page);

  await page.goto(URL);                       // the half v1987 says was never measured
  await page.waitForTimeout(1800);
  const after = await page.evaluate(() => {
    const w: any = window;
    const P = w._D2R_PFX || '';
    // v2084 — the vault left Tools for a main tab of its own, and v2087 made that room open the
    // card on entry. Walking the door he actually walks is what makes the .vm-cell count below a
    // statement about the room rather than about a bare renderVault() call.
    try { w.switchTab && w.switchTab('vault'); } catch (e) {}
    try { w.renderVault && w.renderVault(); } catch (e) {}
    return {
      owned: JSON.parse(localStorage.getItem(P + 'd2r_owned') || '[]'),
      assigned: Object.keys(JSON.parse(localStorage.getItem(P + 'd2r_muleAssign') || '{}')).length,
      cells: document.querySelectorAll('.vm-cell').length,
      grids: document.querySelectorAll('.vm-grid').length,
    };
  });
  expect(after.owned.length, `these vanished on reload: ${BASES.filter((b) => !after.owned.includes(b)).join(', ')}`)
    .toBe(BASES.length);
  expect(after.assigned, 'nothing was filed, so vaultAutoAssign had nothing to work on').toBeGreaterThan(0);
  expect(after.cells, 'the grid is still empty after a reload').toBeGreaterThan(0);
  expect(after.grids).toBeGreaterThan(0);
});

test('auto-assign never overrides a home he chose by hand', async ({ page }) => {
  await cleanWorld(page);
  await page.goto(URL);
  await page.waitForTimeout(1800);
  await applyBases(page);
  const r = await page.evaluate((bases: string[]) => {
    const w: any = window;
    const P = w._D2R_PFX || '';
    const ma = JSON.parse(localStorage.getItem(P + 'd2r_muleAssign') || '{}');
    const name = bases.find((b) => ma[b]) || bases[0];
    const before = ma[name];
    /* MOVE IT THROUGH THE DOOR HIS HAND USES, NOT AROUND IT. This wrote d2r_muleAssign straight
       into localStorage, and `assign` is a closure object loaded ONCE at parse time
       (bible.html:32553) — vaultAutoAssign reads that object and ends on saveA()
       (bible.html:32603, 35100), which serialises it back over any direct write. So the "hand
       move" never existed as far as the app was concerned, and the guard being tested
       (`if (assign[name]) return;`, bible.html:35069) was never actually reached with a
       hand-filed value.
       It read green anyway, for a reason that has since been fixed: before v1980/v1991 taught the
       apply to mule, `ma` came back EMPTY, so `before` was undefined and `other` fell through to
       the '__keep' literal — which is also what suggestMule returns for a keep-in-inventory item.
       The assertion was comparing auto-assign's own answer to itself. [[feedback-blind-fixture-green-gate]]
       window.vaultAssign IS the click-assign handler (assignItem, bible.html:33782/33799), so
       filing through it is the same path a real drag or plate-click takes. It rejects anything
       muleById() does not know, so the target is picked from real assigned ids only — '__keep' is
       not a mule and would silently no-op. */
    const other = Object.keys(ma).map((k) => ma[k])
      .find((id) => id && id !== before && id !== '__keep');
    if (other) { try { w.vaultAssign(name, other); } catch (e) {} }
    const filed = JSON.parse(localStorage.getItem(P + 'd2r_muleAssign') || '{}')[name];
    try { w.vaultAutoAssign && w.vaultAutoAssign(); } catch (e) {}
    const post = JSON.parse(localStorage.getItem(P + 'd2r_muleAssign') || '{}');
    return { name, before, moved: other, filed, after: post[name] };
  }, BASES);
  // NON-VACUITY: a hand move that never landed leaves nothing for auto-assign to override, and the
  // assertion below would pass on an app that does not implement the rule at all.
  expect(r.moved, 'the fixture found no second mule to move it to — nothing was tested').toBeTruthy();
  expect(r.filed, `the hand move did not take: ${r.name} is still on ${r.before}`).toBe(r.moved);
  expect(r.after, `auto-assign moved ${r.name} out of the home it was filed in`).toBe(r.moved);
});
