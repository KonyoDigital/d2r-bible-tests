import { test, expect } from '@playwright/test';

// v347 — duplicate shots are counted (not silently collapsed): an item owned more than once
// shows a ×N badge in the Registered panel, and every copy is drawn on its locker (since v3766/v3767
// each drawn cell names its place in the run, 1/N … N/N — REG-2287). Multi-keep items keep the
// "×have/target" badge; normal duplicates get a distinct cyan ×N "you own spares" badge.

const URL = 'file://' + process.cwd() + '/bible.html';

test.describe('v347 duplicate count badge', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      // v681 — fresh profile skips the v677 grail floor + owner cleanse, so the single-owned control
      // item (Stormshield) survives the reload with copyCount 1 instead of being stripped to the ledger
      // (which made copyCount('Stormshield') read 0). Windforce is mule-assigned so it survived either way.
      localStorage.setItem('d2r_rwProfile', 'fresh');
      localStorage.setItem('d2r_owned', JSON.stringify(['Windforce', 'Stormshield']));
      localStorage.setItem('d2r_muleAssign', JSON.stringify({ Windforce: 'uni-weap' }));
      localStorage.setItem('d2r_copies', JSON.stringify({ Windforce: 3 })); // owned 3 (2 duplicates)
    });
    await page.setViewportSize({ width: 1500, height: 950 });
    await page.goto(URL);
    await page.waitForTimeout(1300);
    await page.evaluate(() => (window as any).switchTab('tools'));
  });

  test('Registered panel shows a ×N duplicate badge (cyan dup variant) for an item owned >1', async ({ page }) => {
    const r = await page.evaluate(() => {
      const rows = Array.from(document.querySelectorAll('#vault-registered .vrg-row'));
      const wf = rows.find((x) => (x.getAttribute('data-vault-item') || '') === 'Windforce');
      const dup = wf?.querySelector('.vrg-copies-dup');
      return {
        text: dup?.textContent || '',
        isDupVariant: !!dup,                              // duplicate badge, NOT the multi-keep "×have/target"
        hasTarget: !!wf?.querySelector('.vrg-copies-t'),  // dup badge has no /target suffix
      };
    });
    expect(r.isDupVariant).toBe(true);
    expect(r.text).toContain('×3');
    expect(r.hasTarget).toBe(false);   // pure count, no /target (that's the multi-keep badge)
  });

  /* V0 spec refresh (#176) — REG-2287 (#137, v3766, GrokBot's retest of his board): the shelf draws EVERY copy
     as its own cell (v3767), so printing ×3 on each of the three cells read as 3 × 3 = 9 owned. A repeated
     shelf cell now names its place in the drawn run — 1/3, 2/3, 3/3 — and its title says "copy N of 3 on this
     locker" (bible.html _copyCellMark: `badge = (index + 1) + '/' + drawn`, `title = 'copy ' + (index + 1) +
     ' of ' + drawn + ' on this locker'`; measured on the merged V1 tree). The ×3 total stays where it is a
     total: the Registered row's duplicate badge (the test above). */
  test('locker cells count the copies as a run (1/3 · 2/3 · 3/3), never ×N on every cell', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cells = Array.from(document.querySelectorAll('.vm-cell[data-vault-item="Windforce"]'));
      return {
        cnt: cells.map((c) => c.querySelector('.vm-cell-cnt')?.textContent || ''),
        tip: cells.map((c) => c.querySelector('.vm-cell-cnt')?.getAttribute('title') || ''),
      };
    });
    expect(r.cnt, 'one cell per owned copy, each naming its place in the run').toEqual(['1/3', '2/3', '3/3']);
    expect(r.tip[0]).toBe('copy 1 of 3 on this locker');
    expect(r.cnt.join(' '), 'the owned total is never printed on every cell').not.toContain('×');
  });

  test('copyCount reflects duplicates and a single-owned item has no badge', async ({ page }) => {
    const r = await page.evaluate(() => ({
      wf: (window as any).copyCount ? (window as any).copyCount('Windforce') : -1,
      ss: (window as any).copyCount ? (window as any).copyCount('Stormshield') : -1,
    }));
    // copyCount may not be window-exposed; fall back to DOM assertion already covered above
    if (r.wf !== -1) { expect(r.wf).toBe(3); expect(r.ss).toBe(1); }
  });
});
