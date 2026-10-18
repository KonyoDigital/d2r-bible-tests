import { test, expect } from '@playwright/test';

// v3767 (Elad 2026-10-18 13:18 IDT) — Grief and Raven Frost stay on the shared mule, so the
// dupes window has no spare cells. With nothing filed and no spares, it is an empty locker.

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

test('a fullscreen dupes window with no spare copies is an empty locker (Elad 2026-10-18)', async ({ page }) => {
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

  expect(r.hasSpareHtml).toBe(false);
  expect(r.open).toBe(true);
  expect(r.spares).toBe(0);
  expect(r.filed).toBe(0);
  expect(r.emptyNotes).toBe(1);
});
