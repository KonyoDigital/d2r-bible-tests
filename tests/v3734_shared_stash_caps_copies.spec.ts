import { test, expect } from '@playwright/test';

// v3767 (Elad 2026-10-18 13:18 IDT) — every physical copy sits on the shared stash.
// A 7-copy Grief draws 7 cells. The old cap of 2 is retired.

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

test('the shared stash draws every copy of a name (Elad 2026-10-18)', async ({ page }) => {
  const r = await page.evaluate((nm) => {
    const seeded = (JSON.parse(localStorage.getItem('d2r_copies') || '{}'))[nm];
    const pack = (window as any)._sharedPack([nm]);
    const cells = ((pack && pack.placed) || []).filter((q: any) => q && q.n === nm).length;
    return { seeded, cells };
  }, NM);
  // the seed took: 7 copies owned, and the shared stash draws all 7
  expect(r.seeded).toBe(7);
  expect(r.cells).toBe(7);
});
