import { test, expect } from '@playwright/test';

// REG-2240 (#108) — review-after-ship on v3740 REG-2227. The copy-undo guard still had a HOLE.
// _vpCopyUndo reverted whatever _vpCopyBump shared the TOKEN. The id checks at the re-roll and clear
// call sites only confirmed the pick being reverted was the one _vpMade points at — NOT that the bump
// record belonged to that pick. _vpCopyBump is replaced ONLY when a pick takes the already-filed branch,
// so a SECOND pick that files fresh (or stays unfiled) leaves the bump sitting on the FIRST pick. A
// re-roll of that second pick (same id, new name) — or a clear — then fired _vpCopyUndo and reverted
// the FIRST pick's copy. Fix: _vpCopyUndo takes the bumped NAME and no-ops unless _vpCopyBump is for it.
//
// Repro: already-filed Grief -> copy 2 (bump = Grief). A DIFFERENT item in the same open moves _vpMade
// to it while the bump STAYS on Grief. Re-rolling that second pick passes the id check and wrongly
// drops Grief's copy.
//
// RED (bug present): after the re-roll, d2r_copies has no Grief (reverted -> copy 1).
// GREEN (fixed): d2r_copies still holds Grief: 2.

const GRIEF = 'Grief';     // a real weapon runeword — routes to a real mule, so pick #1 files 'already' -> copy 2
const SECOND = 'Spirit';   // a DIFFERENT runeword — a different builder id, so _vpMade moves off Grief

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

test('re-rolling a SECOND planner pick must not undo the FIRST pick copy (REG-2240)', async ({ page }) => {
  const r = await page.evaluate(({ grief, second }) => {
    const W = window as any;
    const readCopies = () => { try { return JSON.parse(W.LSR.getItem('d2r_copies') || '{}') || {}; } catch (e) { return {}; } };

    // Only these resolvers are reached through `window.` inside vaultPlannerFile; stub them so each entry
    // resolves to its own name as a runeword. suggestMule / muleById / vaultFile / copies / assign stay the
    // REAL closure (or window) values, so the copy bump and the undo run against the real stores.
    W._cbItem = (id: any) => ({ id });
    W._cbShown = (entry: any) => ({ name: entry && entry.name, q: 'r', base: (entry && entry.base) || '' });
    W._vaultResolveName = (n: any) => n;            // keep the composed name exactly as picked
    W._vaultNameAmbiguity = () => null;             // no kind-settle — the picked name stands
    W.vaultHandAdd = () => ({ ok: true });          // do not mutate the real vault on any pick
    W._vaultPlannerOn = true;                       // defer the per-pick renderVault to planner close

    const token = 'vp-test-138-REG2240';

    // pick #1 — Grief, already filed to uni-weap -> _vpRoute returns mode 'already' -> copy 2, bump = Grief
    const r1 = W.vaultPlannerFile({ id: 'ENTRY-GRIEF', name: grief, base: 'Phase Blade' }, token);
    const afterGrief = readCopies();

    // pick #2 — a DIFFERENT item in the SAME open: _vpMade moves to ENTRY-SECOND, the bump STAYS on Grief
    W.vaultPlannerFile({ id: 'ENTRY-SECOND', name: second, base: 'Monarch' }, token);
    const afterSecond = readCopies();

    // pick #3 — RE-ROLL the second pick (same id, NEW name). The id check matches _vpMade (ENTRY-SECOND),
    // but the stale bump is still Grief's — the hole let _vpCopyUndo revert Grief right here.
    W.vaultPlannerFile({ id: 'ENTRY-SECOND', name: second + ' (vp-reroll)', base: 'Archon Plate' }, token);
    const afterReroll = readCopies();

    return { r1mode: r1 && r1.mode, afterGrief, afterSecond, afterReroll };
  }, { grief: GRIEF, second: SECOND });

  // baseline — pick #1 really filed a SECOND copy of Grief, so there is a bump that CAN be wrongly undone
  expect(r.r1mode, 'the already-filed Grief re-pick is recorded as a copy').toBe('copy');
  expect(r.afterGrief[GRIEF], 'Grief is copy 2 after the first pick').toBe(2);
  // the v3740 id-guard already keeps the copy across a second, DIFFERENT pick
  // REG-2267 (v3753): the different pick in the same open is a swap, so Grief's copy is taken back once
  expect(r.afterSecond[GRIEF], 'the swap takes back the swapped-away copy (REG-2267)').toBeUndefined();

  // REG-2240 (#108): re-rolling the LATER pick must NOT revert Grief's copy — the bump is not Grief's here
  // REG-2240: the re-roll of the later pick must not undo anything more (no double take-back, no negative)
  expect(r.afterReroll[GRIEF], 'a re-roll of a later pick must not touch the earlier copy again').toBeUndefined();
});
