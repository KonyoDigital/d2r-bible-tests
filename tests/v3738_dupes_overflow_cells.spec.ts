import { test, expect } from '@playwright/test';

// v3767 (Elad 2026-10-18 13:18 IDT) — duplicate copies sit next to the original on the same
// mule. GRAIL-DUPES draws no spare cells. A 7-copy shared Grief and a 2-copy Raven Frost both
// contribute 0 overflow. The dupes locker, holding nothing, is an empty locker.
//
// V0 spec refresh (#175 / #176) — HIS 2026-10-22 RULING (verbatim): "so for grief and certain runewords that
// are rare and as hard core as it like last wish too they should be in war gear like 2-3 copies". That retires
// the 10-18 "every copy beside the original on the shared locker" rule FOR WAR GEAR and keeps it for everything
// else, so the two cases are held apart:
//   1. 10-18, a NON-war item. The Stone of Jordan x7 filed to the shared stash: every copy stays on the shared
//      locker (7 cells — a 1x1 ring keeps every copy under his 10-20 cap, bible.html _vaultWarCap0), the
//      GRAIL-DUPES locker draws no spare cells (_vaultDupesCells / _vaultSharedOverflowCells return 0, "v3767
//      no spare cells"), and holding nothing it reads "empty locker" and is dimmed. Grief and Raven Frost left
//      this case: both are on the WAR_GEAR list, and which war items keep every copy is exactly what the
//      10-22 ruling reopened (the exact list is still his to confirm, #175).
//   2. 10-22, war gear. Grief x7 filed to the shared stash keeps 2-3 copies there — on the shelf's shared card
//      AND in the shared stash window, which must agree.
//      ⚠ RED ON THE MERGED V1 TREE, AND THAT IS THE FINDING, NOT A SPEC BUG. Measured: the shelf card draws 4
//      (the 10-20 footprint cap: an un-sized Grief is the 1x2 guess → "small gear" → 4) and the shared stash
//      window draws all 7 (_sharedPack → _sharedCappedCopies, "v3767 draw every copy" — no war cap at all).
//      Two surfaces of one stash disagree, and neither keeps the 2-3 he ruled. It stays red until it is built.

async function seed(page: any, owned: string[], copies: Record<string, number>, assign: Record<string, string>) {
  await page.addInitScript(({ owned, copies, assign }: any) => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      localStorage.setItem('d2r_owned', JSON.stringify(owned));
      localStorage.setItem('d2r_copies', JSON.stringify(copies));
      localStorage.setItem('d2r_muleAssign', JSON.stringify(assign));
    } catch (e) {}
  }, { owned, copies, assign });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any).renderVault === 'function'
    && typeof (window as any)._vaultSharedOverflowCells === 'function');
}

test('the DUPES locker draws no spare cells; copies stay on the shared mule (Elad 2026-10-18)', async ({ page }) => {
  const NAME = 'The Stone of Jordan';
  await seed(page, [NAME], { [NAME]: 7 }, { [NAME]: 'shared' });
  const r = await page.evaluate((nm: string) => {
    const W = window as any;
    const logic = {
      war: W.vaultWarGearRole ? W.vaultWarGearRole(nm) : 'n/a',
      overflow: W._vaultSharedOverflowCells(nm),
      names: W._vaultSharedOverflowNames(),
      sharedCells: W._shelfDrawNames([nm], 'shared').length,
    };
    W.VAULT_PROVEN = { [nm]: true };   // so the ⚖ proof chip renders
    W.renderVault();
    const dupes = document.querySelector('[data-vault-mule="dupes"]');
    const spareCells = dupes ? dupes.querySelectorAll('.vm-spare-sec .vmc-spare').length : -1;
    const nameCells = dupes
      ? Array.from(dupes.querySelectorAll('.vm-spare-sec .vmc-spare'))
          .filter((c: any) => (c.getAttribute('data-arttip') || '').indexOf(nm) >= 0).length
      : -1;
    // REG-2226 follow-up: a dupes locker with ONLY overflow (nothing filed to it) is NOT empty
    const saysEmpty = dupes ? /empty locker/i.test(dupes.textContent || '') : true;
    const isDimmed = dupes ? dupes.classList.contains('vm-empty') : true;
    return { logic, spareCells, nameCells, dupesPresent: !!dupes, saysEmpty, isDimmed };
  }, NAME);

  expect(r.logic.war, 'PREMISE: a non-war item, so the 10-18 rule still governs it').toBeNull();
  expect(r.logic.sharedCells).toBe(7);
  expect(r.dupesPresent).toBe(true);
  expect(r.logic.overflow).toBe(0);
  expect(r.logic.names).not.toContain(NAME);
  expect(r.spareCells).toBe(0);
  expect(r.nameCells).toBe(0);
  expect(r.saysEmpty).toBe(true);
  expect(r.isDimmed).toBe(true);
});

test('war gear keeps 2-3 copies in the war stash, on the shelf card and in the stash window alike (his 2026-10-22 ruling)', async ({ page }) => {
  const NAME = 'Grief';
  await seed(page, [NAME], { [NAME]: 7 }, { [NAME]: 'shared' });
  const r = await page.evaluate((nm: string) => {
    const W = window as any;
    const shelf = W._shelfDrawNames([nm], 'shared').length;
    try { if (typeof W.switchTab === 'function') W.switchTab('tools'); } catch (e) {}
    const tab = W._sharedTabOf(nm).tab;
    W.openMuleCard('shared');
    W._sharedSetPage(tab);
    const windowCells = Array.from(document.querySelectorAll('#vault-detail .vd-item'))
      .filter((el: any) => (el.getAttribute('title') || '').indexOf(nm) === 0).length;
    return { copies: (JSON.parse(localStorage.getItem('d2r_copies') || '{}'))[nm], war: W.vaultWarGearRole(nm),
             filed: W._vaultFiledOn(nm), shelf, windowCells };
  }, NAME);
  expect(r.copies).toBe(7);
  expect(r.war, 'PREMISE: Grief is war gear').toBeTruthy();
  expect(r.filed, 'PREMISE: Grief is filed to the war (shared) stash').toBe('shared');
  // soft, so one run names every surface that is off the ruling (measured today: shelf 4, window 7)
  expect.soft(r.shelf, 'the shelf card keeps 2-3 Grief copies in war gear').toBeGreaterThanOrEqual(2);
  expect.soft(r.shelf, 'the shelf card keeps 2-3 Grief copies in war gear, not the 10-20 cap of 4').toBeLessThanOrEqual(3);
  expect.soft(r.windowCells, 'the shared stash window draws what the shelf card draws — one stash, one count').toBe(r.shelf);
});
