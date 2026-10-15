import { test, expect } from '@playwright/test';

// REG-2226 (#134 E half-2) — his rule E: the shared stash keeps 2 copies of a name; the 3rd+ is trade-stock
// held in GRAIL-DUPES, thrown out NEVER. v3734/v3737 capped the shared VIEW at 2; this SHOWS the overflow in
// the DUPES locker as display-only "spare" cells. The item stays homed in 'shared' (not re-filed), so the
// spare cells carry no ✕; the true total is the registered ×N. No double-count: shared draws 2, dupes draws
// min(copies-2, _MULE_COPY_CAP).
//
// RED without the fix: the helpers don't exist and the dupes card has no .vmc-spare cells. GREEN: a 7-copy
// shared item contributes 3 spare cells (min(7-2,3)); a 2-copy item contributes none.

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

test('the DUPES locker shows overflow copies (>2) of a shared item as spare cells (REG-2226)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const W = window as any;
    const logic = {
      griefOverflow: W._vaultSharedOverflowCells('Grief'),       // min(7-2, 3) = 3
      ravenOverflow: W._vaultSharedOverflowCells('Raven Frost'), // 2-2 = 0
      names: W._vaultSharedOverflowNames(),
    };
    W.renderVault();
    const dupes = document.querySelector('[data-vault-mule="dupes"]');
    const spareCells = dupes ? dupes.querySelectorAll('.vm-spare-sec .vmc-spare').length : -1;
    const griefCells = dupes
      ? Array.from(dupes.querySelectorAll('.vm-spare-sec .vmc-spare'))
          .filter((c: any) => (c.getAttribute('data-arttip') || '').indexOf('Grief') >= 0).length
      : -1;
    return { logic, spareCells, griefCells, dupesPresent: !!dupes };
  });

  // the overflow LOGIC: 7 copies → 3 spare cells (capped), 2 copies → 0
  expect(r.logic.griefOverflow).toBe(3);
  expect(r.logic.ravenOverflow).toBe(0);
  expect(r.logic.names).toContain('Grief');
  expect(r.logic.names).not.toContain('Raven Frost');
  // the RENDER: the dupes locker draws exactly those 3 spare cells, all Grief
  expect(r.dupesPresent).toBe(true);
  expect(r.spareCells).toBe(3);
  expect(r.griefCells).toBe(3);
});
