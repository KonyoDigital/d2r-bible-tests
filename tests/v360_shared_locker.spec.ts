// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';

// v360/v364 — SHARED STASH = general cross-account storage (the 5 in-game shared tabs). It's a normal
// assignable locker filled by AUTO-SORT during intake (high-value "worth keeping close" items) — NOT
// runes/gems/materials (those have their own planners). Runes/sunders stay out of the draggable dock.

const URL = 'file://' + process.cwd() + '/bible.html';

test('SHARED STASH locker exists; holds items assigned to it (not runes/mats)', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Annihilus', 'Windforce', 'Ber Rune']));
    localStorage.setItem('d2r_muleAssign', JSON.stringify({ Annihilus: 'shared', Windforce: 'uni-weap' }));
  });
  await page.setViewportSize({ width: 1500, height: 950 });
  await page.goto(URL);
  await page.waitForTimeout(1500);
  await page.evaluate(() => (window as any).switchTab('tools'));
  const r = await page.evaluate(() => {
    const shared = document.querySelector('.vault-mule[data-vault-mule="shared"]');
    const cells = shared ? Array.from(shared.querySelectorAll('.vm-cell')).map((c) => c.getAttribute('data-vault-item')) : [];
    const dock = Array.from(document.querySelectorAll('.vault-chip')).map((c) => c.getAttribute('data-vault-item'));
    return { hasSharedLocker: !!shared, cells, dockHasBer: dock.includes('Ber Rune') };
  });
  expect(errs).toEqual([]);
  expect(r.hasSharedLocker).toBe(true);
  expect(r.cells).toContain('Annihilus');   // assigned here → shows in the SHARED locker
  expect(r.cells).not.toContain('Windforce'); // assigned to a mule, not shared
  expect(r.dockHasBer).toBe(false);          // runes (shared-stash type) stay OUT of the mule dock
});
