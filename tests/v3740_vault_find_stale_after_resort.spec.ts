import { test, expect } from '@playwright/test';

// REG-2230 (#12) — Vault FIND had two JOINED defects:
//   1) FRESHNESS: vaultFind re-ran ONLY on type / clear, so after a re-sort, move or unfile the rows
//      (and the location + click target baked into each) kept pointing at where an item USED to be.
//      FIX: renderVault — the one hub every re-sort funnels through — now calls window._vaultFindRefresh.
//   2) CLICK TARGET: a shared-stash row opened openMuleCard('shared'), which draws _sharedPage; that
//      defaults to 0 (the Weapons tab) and the open never changed it, so EVERY shared row opened
//      "Shared Stash > Weapons". FIX: a shared row now opens window._sharedSetPage(_sharedTabOf(n).tab)
//      — the exact tab the item is packed on. (#79 then kept the click on the vault; #144.10 shared half, REG-2801,
//      replaced the by-slot tabs and _sharedTabOf with the plan's 5 pages - the click assertion below is what stands.)
//
// RED without the fix: test 1 lands on Page 1 / 5 (Weapons) not the item's tab; test 2 keeps the stale
// mule. GREEN with the fix: the click lands on the item's real tab, and the finder repaints after a move.
// Seeds via localStorage only (fixtures never touch live data). Not run here — CI / his Mac only.

const URL = 'file://' + process.cwd() + '/bible.html';

async function openVault(page: any) {
  await page.setViewportSize({ width: 1500, height: 950 });
  await page.goto(URL);
  await page.waitForFunction(() => (window as any).vaultFind && (window as any).renderVault
    && (window as any)._sharedLayout && (window as any)._sharedSetPage && (window as any).vaultFile
    && (window as any)._vaultWhereIs);
  await page.evaluate(() => (window as any).switchTab('tools'));
}

test.describe('REG-2230 vault FIND freshness + click target', () => {
  test('a shared-stash FIND row knows the item tab but the click stays on the vault (#79)', async ({ page }) => {
    await page.addInitScript(() => {
      // v681 — a fresh profile skips the grail floor + owner cleanse so a seeded owned item survives reload.
      localStorage.setItem('d2r_rwProfile', 'fresh');
      localStorage.setItem('d2r_owned', JSON.stringify(['Arachnid Mesh']));           // a belt unique
      localStorage.setItem('d2r_muleAssign', JSON.stringify({ 'Arachnid Mesh': 'shared' }));
    });
    await openVault(page);
    const r = await page.evaluate(() => {
      const w = window as any;
      // REG-2801 - the page FIND names for it (the shared stash is its 5 pages now, not by-slot tabs)
      const cell = String(((w._vaultWhereIs('Arachnid Mesh') || {}).cell) || '');
      w.vaultFind('arachnid');
      const row = document.querySelector('#vault-find-results .vfr-row') as HTMLElement | null;
      const had = !!row;
      if (row) row.click();                 // fires the row's REAL inline onclick
      return {
        had,
        cell,
        cardOpen: !((document.getElementById('vault-detail') as HTMLElement) || { hidden: true }).hidden,
        activeTab: (document.querySelector('#vault-detail .vd-tab.vt-on')?.textContent || ''),
        pagebar: (document.querySelector('#vault-detail .vd-pagebar')?.textContent || ''),
      };
    });
    expect(r.had, 'the finder must list the owned shared-stash item').toBe(true);
    expect(r.cell, 'FIND names no shared-page cell for the filed belt').toMatch(/^Page [1-5] · col \d+ · row \d+$/);
    // #79 — the finder still names the item's cell (asserted above), but the click no longer
    // opens the shared stash page: it stays on the vault (his "page trap" is gone). The floating HD card is
    // the finder-row affordance now, covered by tests/v3741_vault_find_row_stays_on_vault.spec.ts.
    expect(r.cardOpen, 'a FIND-row click opens no shared stash page - it stays on the vault (#79)').toBe(false);
  });

  test('FIND refreshes after a re-sort/move instead of showing the stale locker', async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('d2r_rwProfile', 'fresh');
      localStorage.setItem('d2r_owned', JSON.stringify(['Windforce']));               // a bow -> uni-weap
      localStorage.setItem('d2r_muleAssign', JSON.stringify({ Windforce: 'uni-weap' }));
    });
    await openVault(page);
    const r = await page.evaluate(() => {
      const w = window as any;
      const inp = document.getElementById('vault-find-input') as HTMLInputElement;
      inp.value = 'windforce';              // what his typing leaves in the box (the refresh reads it)
      w.vaultFind('windforce');             // render the finder
      const muleOf = () => (document.querySelector('#vault-find-results .vfr-row .vfr-mule')?.textContent || '').toUpperCase();
      const before = muleOf();
      const mv = w.vaultFile('Windforce', null, { move: true, mule: 'uni-armor' });    // a re-sort-style move
      const modelMule = (((w._vaultWhereIs('Windforce') || {}).muleName) || '').toUpperCase();
      w.renderVault();                      // the redraw every re-sort funnels through
      const after = muleOf();
      return { before, ok: !!(mv && mv.ok), modelMule, after };
    });
    expect(r.before, 'the item starts filed in UNI-WEAPONS').toContain('UNI-WEAPONS');
    expect(r.ok, 'the move must land in the model').toBe(true);
    expect(r.modelMule, 'the model really moved to UNI-ARMOR').toContain('UNI-ARMOR');
    // GREEN: the open finder repaints to UNI-ARMOR. RED: it stays stale on UNI-WEAPONS.
    expect(r.after, 'FIND must refresh to the new locker after the re-sort').toContain('UNI-ARMOR');
  });
});
