import { test, expect } from '@playwright/test';

// v3767 (Elad 2026-10-18 13:18 IDT) — duplicate copies sit next to the original on the same
// mule. GRAIL-DUPES draws no spare cells. A 7-copy shared Grief and a 2-copy Raven Frost both
// contribute 0 overflow. The dupes locker, holding nothing, is an empty locker.

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
  await page.waitForFunction(() => typeof (window as any).renderVault === 'function'
    && typeof (window as any)._vaultSharedOverflowCells === 'function');
});

test('the DUPES locker draws no spare cells; copies stay on the shared mule (Elad 2026-10-18)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const W = window as any;
    const logic = {
      griefOverflow: W._vaultSharedOverflowCells('Grief'),
      ravenOverflow: W._vaultSharedOverflowCells('Raven Frost'),
      names: W._vaultSharedOverflowNames(),
      sharedGrief: W._shelfDrawNames(['Grief'], 'shared').length,
    };
    W.VAULT_PROVEN = { 'Grief': true };   // so the ⚖ proof chip renders and we can check its numerator
    W.renderVault();
    const dupes = document.querySelector('[data-vault-mule="dupes"]');
    const spareCells = dupes ? dupes.querySelectorAll('.vm-spare-sec .vmc-spare').length : -1;
    const griefCells = dupes
      ? Array.from(dupes.querySelectorAll('.vm-spare-sec .vmc-spare'))
          .filter((c: any) => (c.getAttribute('data-arttip') || '').indexOf('Grief') >= 0).length
      : -1;
    // REG-2226 follow-up: a dupes locker with ONLY overflow (nothing filed to it) is NOT empty
    const saysEmpty = dupes ? /empty locker/i.test(dupes.textContent || '') : true;
    const isDimmed = dupes ? dupes.classList.contains('vm-empty') : true;
    // the ⚖ proof chip: a proven overflow name must count in BOTH numerator and denominator
    const provEl = dupes ? dupes.querySelector('.vm-proven') : null;
    // the chip's visible text is "⚖ <seen>"; the "of <denominator>" lives in its title attribute
    const provSeen = provEl ? String(provEl.textContent || '').replace(/[^0-9]/g, '') : '';
    const provTitle = provEl ? String(provEl.getAttribute('title') || '') : '';
    return { logic, spareCells, griefCells, dupesPresent: !!dupes, saysEmpty, isDimmed, provSeen, provTitle };
  });

  expect(r.logic.sharedGrief).toBe(7);
  expect(r.dupesPresent).toBe(true);
  expect(r.logic.griefOverflow).toBe(0);
  expect(r.logic.ravenOverflow).toBe(0);
  expect(r.logic.names).not.toContain('Grief');
  expect(r.logic.names).not.toContain('Raven Frost');
  expect(r.spareCells).toBe(0);
  expect(r.griefCells).toBe(0);
  expect(r.saysEmpty).toBe(true);
  expect(r.isDimmed).toBe(true);
});
