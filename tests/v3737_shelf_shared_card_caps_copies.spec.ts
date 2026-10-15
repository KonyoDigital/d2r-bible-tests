import { test, expect } from '@playwright/test';

// REG-2225 — the shelf shared-stash CARD draws one cell per copy (its grid is drawn.map over
// _shelfDrawNames). v3734 capped the FULLSCREEN shared view (_sharedPack/_sharedCappedCopies) at 2 but left
// _shelfCopyCount UNCAPPED for 'shared' (`if (muleId !== 'shared') c = min(c, cap)`), so a 7-copy item still
// showed 7 tiles on the shelf card while the fullscreen showed 2 — the "copy 7 filed to shared" GrokBot saw.
// Now _shelfCopyCount caps 'shared' at _SHARED_COPY_CAP (2) and every other locker at _MULE_COPY_CAP (3), so
// the two surfaces agree. (The shared card never calls _muleLoad — _isMule is false for it — so this is the
// only cap path for its grid.)
//
// RED without the fix: _shelfDrawNames(['Grief'],'shared').length === 7. GREEN: === 2. A non-shared mule
// stays at 3 — the control proving the cap is shared-specific, not a global change.

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

test('the shelf shared card caps a name at 2 cells, matching the fullscreen (REG-2225)', async ({ page }) => {
  const r = await page.evaluate((nm) => ({
    seededCopies: (JSON.parse(localStorage.getItem('d2r_copies') || '{}'))[nm],
    sharedCells: (window as any)._shelfDrawNames([nm], 'shared').length,
    muleCells: (window as any)._shelfDrawNames([nm], 'uni-weap').length,
  }), NAME);
  // the seed took: 7 copies owned
  expect(r.seededCopies).toBe(7);
  // REG-2225: the shelf SHARED card draws at most 2 cells (was 7, uncapped)
  expect(r.sharedCells).toBe(2);
  // control: a non-shared mule still caps at 3 — the cap change is shared-specific
  expect(r.muleCells).toBe(3);
});
