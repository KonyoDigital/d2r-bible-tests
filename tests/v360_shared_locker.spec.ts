import { test, expect } from '@playwright/test';

// v360 — never-muled items (runes/essences/Worldstone shards/Colossal statues/sunders) get a dedicated
// SHARED STASH locker tile + stay out of the draggable "unsorted" dock.

const URL = 'file://' + process.cwd() + '/bible.html';

test('shared-stash items land in the SHARED STASH locker, not the dock', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Ber Rune', 'Twisted Essence of Suffering', 'Cold Rupture', 'Windforce']));
  });
  await page.setViewportSize({ width: 1500, height: 950 });
  await page.goto(URL);
  await page.waitForTimeout(1500);
  await page.evaluate(() => (window as any).switchTab('tools'));
  const r = await page.evaluate(() => {
    const shared = document.querySelector('.vault-mule[data-vault-mule="shared"]');
    const cells = shared ? Array.from(shared.querySelectorAll('.vm-cell')).map((c) => c.getAttribute('data-vault-item')) : [];
    const dock = Array.from(document.querySelectorAll('#vault-dock .vault-chip, .vault-chip')).map((c) => c.getAttribute('data-vault-item'));
    return { hasSharedLocker: !!shared, cells, dockHasBer: dock.includes('Ber Rune'), dockHasWindforce: dock.includes('Windforce') };
  });
  expect(errs).toEqual([]);
  expect(r.hasSharedLocker).toBe(true);
  expect(r.cells).toContain('Ber Rune');
  expect(r.cells).toContain('Cold Rupture');           // sunder
  expect(r.cells).toContain('Twisted Essence of Suffering');
  expect(r.dockHasBer).toBe(false);                    // NOT in the unsorted dock anymore
});
