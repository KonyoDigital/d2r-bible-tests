import { test, expect } from '@playwright/test';

// REG-2227 (#3 vault-planner copy-undo) — picking a SECOND, DIFFERENT item in ONE planner open must
// not undo the copy bump the item picked before it earned. vaultPlannerFile's name-change branch
// (bible.html ~45138) called _vpCopyUndo whenever the composed name differed from the last pick, with
// NO id guard, so it fired "whatever the id". Dock scenario: Grief is already filed, re-picking it files
// copy 2, then a pick of a DIFFERENT item in the same open (same token, different builder id) dropped
// Grief back to copy 1. The _vpDrop sibling one line below already guards with `_vpMade.id === entry.id`;
// the copy-undo must match it so it only fires on a RE-ROLL of the SAME pick, never on a new second item.
//
// RED (bug present): after the second pick d2r_copies has no Grief (undone -> copy 1).
// GREEN (fixed): d2r_copies still holds Grief: 2.

const GRIEF = 'Grief';     // a real weapon runeword — survives the owned-prune, routes to uni-weap
const SECOND = 'Spirit';   // a DIFFERENT real runeword — different builder id, different name

test.beforeEach(async ({ page }) => {
  await page.addInitScript((nm) => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      localStorage.setItem('d2r_owned', JSON.stringify([nm]));
      localStorage.setItem('d2r_copies', JSON.stringify({}));                        // owned x1 to start
      localStorage.setItem('d2r_muleAssign', JSON.stringify({ [nm]: 'uni-weap' }));  // already filed -> 'already'
    } catch (e) {}
  }, GRIEF);
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any).vaultPlannerFile === 'function'
    && !!(window as any).LSR);
});

test('a second, different planner pick keeps the first pick copy (REG-2227)', async ({ page }) => {
  const r = await page.evaluate(({ grief, second }) => {
    const W = window as any;
    const readCopies = () => { try { return JSON.parse(W.LSR.getItem('d2r_copies') || '{}') || {}; } catch (e) { return {}; } };

    // Only these four resolvers are reached through `window.` inside vaultPlannerFile; stub them so each
    // entry resolves to its own name as a runeword. suggestMule / muleById / copies / assign stay the
    // REAL closure values, so the copy bump and the undo run against the real stores.
    W._cbItem = (id: any) => ({ id });
    W._cbShown = (entry: any) => ({ name: entry && entry.name, q: 'r', base: (entry && entry.base) || '' });
    W._vaultResolveName = (n: any) => n;           // keep the composed name exactly as picked
    W.vaultHandAdd = () => ({ ok: true });          // do not mutate the real vault on either pick
    W._vaultPlannerOn = true;                       // defer the per-pick renderVault to planner close

    const token = 'vp-test-108-REG2227';

    // pick #1 — Grief, already filed to uni-weap -> _vpRoute returns mode 'already' -> copy 2
    const r1 = W.vaultPlannerFile({ id: 'ENTRY-GRIEF', name: grief, base: 'Phase Blade' }, token);
    const afterGrief = readCopies();

    // pick #2 — a DIFFERENT item in the SAME open (same token, different id + name)
    const r2 = W.vaultPlannerFile({ id: 'ENTRY-SECOND', name: second, base: 'Monarch' }, token);
    const afterSecond = readCopies();

    return { r1mode: r1 && r1.mode, r2mode: r2 && r2.mode, afterGrief, afterSecond };
  }, { grief: GRIEF, second: SECOND });

  // baseline — the first pick really filed a SECOND copy of Grief, so the undo has something to undo
  expect(r.r1mode, 'the already-filed Grief re-pick is recorded as a copy').toBe('copy');
  expect(r.afterGrief[GRIEF], 'Grief is copy 2 after the first pick').toBe(2);

  // REG-2227 (#3): picking a DIFFERENT item next must NOT undo Grief's copy — whatever its id
  expect(r.afterSecond[GRIEF], 'a later, different pick must not undo the earlier copy').toBe(2);
});
