import { test, expect } from '@playwright/test';

// REG-2224 (#10 count-sync) — GrokBot #230: "cards count cells not items (329 vs 220)". A locker card's
// count badge showed `total = drawn.length + magicItems.length`, and _shelfDrawNames pushes a name ONCE PER
// COPY (the grid draws a cell per copy), so `total` is COPIES — while the badge's own title says "N item(s)",
// the Registered header counts NAMES, and the ⚖ proven chip counts names. So a locker with one unique owned
// ×3 showed "3" labelled "3 items". The fix adds _itemN (distinct names + magic keepers) for the badge, its
// label and the proven denominator (and dedups the proven numerator); `cells` (copies) stays as the title's
// "N cells" so duplicates are never hidden.
//
// RED without the fix: the uni-weap card badge reads "3" (copies). GREEN with the fix: it reads "1" (one
// distinct item), and the title still says "3 cells".

const NAME = "Griswold's Edge"; // a weapon unique → assigned to the uni-weap locker, owned ×3

test.beforeEach(async ({ page }) => {
  await page.addInitScript((nm) => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      localStorage.setItem('d2r_owned', JSON.stringify([nm]));
      localStorage.setItem('d2r_copies', JSON.stringify({ [nm]: 3 }));
      localStorage.setItem('d2r_muleAssign', JSON.stringify({ [nm]: 'uni-weap' }));
    } catch (e) {}
  }, NAME);
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any).renderVault === 'function'
    && typeof (window as any)._shelfDrawNames === 'function');
});

test('a locker card counts distinct ITEMS, not copies (REG-2224)', async ({ page }) => {
  const r = await page.evaluate((nm) => {
    try { (window as any).renderVault(); } catch (e) {}
    const card = document.querySelector('[data-vault-mule="uni-weap"]');
    const countEl = card ? card.querySelector('.vm-count') : null;
    // copies filed to this mule, straight from the source the card uses
    const copies = (window as any)._shelfDrawNames([nm], 'uni-weap').length;
    return {
      present: !!card,
      badge: countEl ? String(countEl.textContent || '').trim() : null,
      title: countEl ? String(countEl.getAttribute('title') || '') : '',
      copies,
    };
  }, NAME);

  // the item is filed to uni-weap with 3 physical copies (the grid draws 3 cells)
  expect(r.present, 'the uni-weap locker card should render').toBe(true);
  expect(r.copies, 'the source counts 3 copies filed here').toBe(3);
  // REG-2224: the BADGE shows 1 distinct ITEM, not 3 copies
  expect(r.badge, 'the badge counts distinct items, not copies').toBe('1');
  // ...and the label agrees it is 1 item, while copies are preserved as "3 cells"
  expect(r.title).toMatch(/\b1 item\b/);
  expect(r.title).toContain('3 cells');
});
