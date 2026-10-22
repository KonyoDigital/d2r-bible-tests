import { test, expect } from '@playwright/test';

// #76 (phase 2) — SET-PIECE NAME RECONCILE folds a duplicate name-form into ONE at load.
// GrokBot read his board (#230): "Natalya's Totem" (bare) and "Natalya's Totem (helm)" (slotted) were the
// SAME helm under two names — counted twice, and "Delete unsorted" left the other form in the mule. v3750
// deduped the FIND display; this reconciles the DATA. _setPieceReconcile is one-time (d2r_setPieceReconcile
// stamp), journaled via vaultRemove (undoable with vaultRestoreLast), and scoped to window._vfCanon (known
// set pieces only). It keeps the CANONICAL slotted name and removes the bare — but ONLY when no filing is
// lost (keeper already filed, or the leaving form loose); it SPARES the reversed case, because a dropped
// mule filing is data loss.
// RED WITHOUT THE MIGRATION: window._setPieceReconcile is undefined -> res.folded throws (test errors).
// Verified via CDP on the real page: fold 3->2 keeping the filed (helm); spare when the bare is the filed one.
// [[the-unjoined-end]] [[unknown-stays-unknown]] [[regression-guard]]

const URL = 'file://' + process.cwd() + '/bible.html';
const BARE = "Natalya's Totem", HELM = "Natalya's Totem (helm)";

async function seedLoad(page: any, owned: string[], assign: any) {
  await page.addInitScript(({ owned, assign }: any) => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      Object.defineProperty(navigator, 'webdriver', { get: () => true });
      localStorage.setItem('d2r_owned', JSON.stringify(owned));
      localStorage.setItem('d2r_muleAssign', JSON.stringify(assign));
      localStorage.setItem('d2r_copies', '{}');
      // v3753 runs the fold once at LOAD; stamp it done so the test's forced run is the one under test
      localStorage.setItem('d2r_setPieceReconcile', JSON.stringify({ ver: 99 }));
      // and the older REG-2229 set-dupe migration would fold a loose twin at load first
      localStorage.setItem('d2r_setDupeMigrate_v2227', '1');
    } catch (e) {}
  }, { owned, assign });
  await page.goto(URL);
  await page.waitForFunction(() =>
    (window as any)._setPieceReconcile && (window as any).ownedPool && (window as any).vaultRemove);
}

async function run(page: any) {
  return await page.evaluate(() => {
    const w = window as any;
    const before = w.ownedPool().filter((n: string) => /Natalya|Raven/.test(n));
    const res = w._setPieceReconcile({ force: true });
    const after = w.ownedPool().filter((n: string) => /Natalya|Raven/.test(n));
    let am: any = {}; try { am = JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}'); } catch (e) {}
    return { folded: res.folded || [], spared: res.spared || [], before, after,
             assignHelm: am["Natalya's Totem (helm)"] || null, assignBare: am["Natalya's Totem"] || null,
             restorable: typeof w.vaultRestoreLast === 'function' };
  });
}

test('folds a set-piece dup to one, keeps the filed slotted form, journaled (#76)', async ({ page }) => {
  await seedLoad(page, [BARE, HELM, 'Raven Frost'], { [HELM]: 'sets-rest' });
  const r = await run(page);
  expect(r.before).toContain(BARE);          // the dup was there (seed is live)
  expect(r.folded).toEqual([BARE]);          // the bare form folded away
  expect(r.after).toContain(HELM);           // the canonical slotted stays
  expect(r.after).not.toContain(BARE);       // the bare is gone
  expect(r.after).toContain('Raven Frost');  // a unique is untouched
  expect(r.assignHelm).toBe('sets-rest');    // the filing is preserved
  expect(r.restorable).toBe(true);           // journaled / undoable
});

test('spares a dup when folding would drop a filing — no data loss (#76)', async ({ page }) => {
  // the BARE form is the one filed (the keeper would be loose) -> folding must NOT drop its mule cell
  await seedLoad(page, [BARE, HELM, 'Raven Frost'], { [BARE]: 'sets-rest' });
  const r = await run(page);
  expect(r.folded).toEqual([]);              // nothing folded
  expect(r.spared.length).toBe(1);           // the pair is spared instead
  expect(r.after).toContain(BARE);           // both forms remain
  expect(r.after).toContain(HELM);
  expect(r.assignBare).toBe('sets-rest');    // the filing stays put
});

test('no duplicate -> no-op (#76)', async ({ page }) => {
  await seedLoad(page, [HELM, 'Raven Frost'], { [HELM]: 'sets-rest' });
  const r = await run(page);
  expect(r.folded).toEqual([]);
  expect(r.after).toContain(HELM);
  expect(r.after).toContain('Raven Frost');
});
