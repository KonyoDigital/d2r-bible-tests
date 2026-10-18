import { test, expect } from '@playwright/test';

// v3767 (Elad 2026-10-18 13:18 IDT) — the shelf draws every physical copy, on the shared
// locker and on a category mule. A 7-copy Grief is 7 cells on both.

const NAME = 'Grief';

test.beforeEach(async ({ page }) => {
  await page.addInitScript((nm) => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      localStorage.setItem('d2r_owned', JSON.stringify([nm]));
      localStorage.setItem('d2r_copies', JSON.stringify({ [nm]: 7 }));
    } catch (e) {}
  }, NAME);
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any)._shelfDrawNames === 'function');
});

test('the shelf draws every copy on the shared locker and on a mule (Elad 2026-10-18)', async ({ page }) => {
  const r = await page.evaluate((nm) => ({
    seededCopies: (JSON.parse(localStorage.getItem('d2r_copies') || '{}'))[nm],
    sharedCells: (window as any)._shelfDrawNames([nm], 'shared').length,
    muleCells: (window as any)._shelfDrawNames([nm], 'uni-weap').length,
  }), NAME);
  expect(r.seededCopies).toBe(7);
  expect(r.sharedCells).toBe(7);
  expect(r.muleCells).toBe(7);
});
