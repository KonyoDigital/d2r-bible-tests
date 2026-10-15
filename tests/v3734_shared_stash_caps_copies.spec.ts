import { test, expect } from '@playwright/test';

// REG-2222 — his rule 2026-10-15: the SHARED STASH keeps at most 2 copies of a name; a 3rd+ copy is
// trade-stock, not a 3rd shared cell. _sharedPack drew copyCount cells, so GrokBot saw "copy 7 filed
// to shared". _sharedCappedCopies now caps the cells (and _sharedCopyTotal with it, so the count and
// the grid can never disagree). The true ownership (copies[name]) is unchanged — the ×N still shows in
// the registered view; the overflow renders as duplicates-mule cells in the follow-up (half 2).

const NM = 'Grief';

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  // seed 7 owned copies through the real store, then reload so the module loads them into copies[]
  await page.evaluate((nm) => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      localStorage.setItem('d2r_copies', JSON.stringify({ [nm]: 7 }));
      const owned = JSON.parse(localStorage.getItem('d2r_owned') || '[]');
      if (owned.indexOf(nm) < 0) owned.push(nm);
      localStorage.setItem('d2r_owned', JSON.stringify(owned));
    } catch (e) {}
  }, NM);
  await page.reload();
  await page.waitForFunction(() => typeof (window as any)._sharedPack === 'function');
});

test('the shared stash caps a name at 2 cells, however many copies are owned (REG-2222)', async ({ page }) => {
  const r = await page.evaluate((nm) => {
    const seeded = (JSON.parse(localStorage.getItem('d2r_copies') || '{}'))[nm];
    const pack = (window as any)._sharedPack([nm]);
    const cells = ((pack && pack.placed) || []).filter((q: any) => q && q.n === nm).length;
    return { seeded, cells };
  }, NM);
  // the seed took: 7 copies owned (the ownership itself is NOT capped — only the shared display is)
  expect(r.seeded).toBe(7);
  // ...and the shared stash draws at most 2 cells of it (was 7 before REG-2222 — "copy 7 filed to shared")
  expect(r.cells).toBe(2);
});
