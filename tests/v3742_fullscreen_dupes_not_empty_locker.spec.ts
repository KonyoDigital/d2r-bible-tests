import { test, expect } from '@playwright/test';

// REG-2240 (#134 fullscreen follow-up, review-after-ship on v3740) — a FULLSCREEN dupes window
// (openMuleCard('dupes')) whose ONLY content is shared spare-overflow copies must NOT also paint the
// "empty locker" placeholder (a dimmed .vm-empty note). v3740/REG-2231 appended the spare cells to
// mp-main, but the notes section still emitted the placeholder because its guard only checked filed
// names + dbPlaced, not the spare html — so the window showed the spare cells AND said "empty".
// This mirrors the v3739 SHELF fix (REG-2226 follow-up): a non-empty spare html suppresses the note.
//
// Scenario: Grief x7 and Raven Frost x2, BOTH homed in 'shared' (nothing filed to 'dupes'). The dupes
// window therefore has no filed items — only the 3 capped Grief spare cells.
// RED without the fix: the window shows 3 spare cells AND the empty-locker note (emptyNotes === 1).
// GREEN with the fix: the 3 spare cells show and the note is gone (emptyNotes === 0).

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      localStorage.setItem('d2r_owned', JSON.stringify(['Grief', 'Raven Frost']));
      localStorage.setItem('d2r_copies', JSON.stringify({ 'Grief': 7, 'Raven Frost': 2 }));
      localStorage.setItem('d2r_muleAssign', JSON.stringify({ 'Grief': 'shared', 'Raven Frost': 'shared' }));
    } catch (e) {}
  });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any).openMuleCard === 'function'
    && typeof (window as any).renderVault === 'function'
    && typeof (window as any)._muleNamesFor === 'function'
    && typeof (window as any)._vaultSharedOverflowHtml === 'function');
});

test('a fullscreen dupes window with only shared spare copies is NOT an empty locker (REG-2240)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const W = window as any;
    W.renderVault();
    // the dupes locker has NOTHING filed to it — both items are homed in 'shared'
    const filed = W._muleNamesFor('dupes').length;
    // ...but the shared overflow (Grief's 3rd..5th copies, capped at 3) renders spare cells
    const spareHtml = W._vaultSharedOverflowHtml();
    W.openMuleCard('dupes');
    const box = document.getElementById('vault-detail');
    const open = !!box && !box.hidden;
    const spares = box ? box.querySelectorAll('.vm-spare-sec .vmc-spare').length : -1;
    // the "empty locker — assign items..." placeholder is a dimmed .vm-empty note
    const emptyNotes = box
      ? Array.from(box.querySelectorAll('.vm-empty')).filter((e: any) => /empty locker/i.test(e.textContent || '')).length
      : -1;
    if (W.vaultCloseCard) W.vaultCloseCard();
    return { filed, hasSpareHtml: /vm-spare-sec/.test(spareHtml), open, spares, emptyNotes };
  });

  // premise first: the overflow is really there, the window opened, and the spare cells drew.
  // a filed count of 0 with no spare cells is just an empty locker, and that zero proves nothing.
  expect(r.hasSpareHtml).toBe(true);
  expect(r.open).toBe(true);
  // the spare cells ARE drawn (3 capped Grief spares) — REG-2231
  expect(r.spares).toBe(3);
  // nothing is filed to dupes — the only content is those spare cells
  expect(r.filed).toBe(0);
  // ...and the window does NOT also say "empty locker" — REG-2240
  expect(r.emptyNotes).toBe(0);
});
