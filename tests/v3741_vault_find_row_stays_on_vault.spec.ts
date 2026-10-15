import { test, expect } from '@playwright/test';

// #79 (REG-2238) - Vault FIND row PAGE TRAP. His words (#230 6125174498): "everything should be smooth".
// A FIND-row click used to ROUTE off the finder: a shared item opened the full Shared Stash page (REG-2230
// made it land on the right TAB, but opening at all was the trap he hit), a mule item opened its ID card.
// He wants only the floating HD tooltip and to STAY on the vault - the rule the locker tiles already follow
// (the v169 keep-open list). This mirrors it onto .vfr-row: the row carries NO nav, and a click KEEPS the
// floating card instead of dismissing it.
//
// RED without the fix: clicking the shared row opens #vault-detail (the shared stash page) AND the v169
// click handler dismisses the floating card (#arttip loses .on), because .vfr-row is not on the keep-open
// list. GREEN with it: #vault-detail stays hidden and #arttip stays .on, so he never leaves the finder.
// Seeds via localStorage only (fixtures never touch live data). NOT run here - CI / his Mac only.

const URL = 'file://' + process.cwd() + '/bible.html';

async function openVault(page: any) {
  await page.setViewportSize({ width: 1500, height: 950 });
  await page.goto(URL);
  await page.waitForFunction(() => (window as any).vaultFind && (window as any).renderVault
    && (window as any)._vaultWhereIs && (window as any)._sharedTabOf);
  await page.evaluate(() => (window as any).switchTab('tools'));
}

test.describe('#79 vault FIND row stays on the vault', () => {
  test('a shared FIND-row click opens no page and keeps the floating HD card', async ({ page }) => {
    await page.addInitScript(() => {
      // v681 - a fresh profile skips the grail floor + owner cleanse so a seeded owned item survives reload.
      localStorage.setItem('d2r_rwProfile', 'fresh');
      localStorage.setItem('d2r_owned', JSON.stringify(['Arachnid Mesh']));            // a belt unique
      localStorage.setItem('d2r_muleAssign', JSON.stringify({ 'Arachnid Mesh': 'shared' }));
    });
    await openVault(page);
    const r = await page.evaluate(() => {
      const w = window as any;
      w.vaultFind('arachnid');
      const row = document.querySelector('#vault-find-results .vfr-row') as HTMLElement | null;
      const art = row ? (row.querySelector('.d2art-wrap[aria-label]') as HTMLElement | null) : null;
      // open the floating HD card by hovering the item art (the finder row's compact arttip anchor)
      if (art) art.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
      const tip = document.getElementById('arttip');
      const tipOpenedOnHover = !!(tip && tip.classList.contains('on'));
      // his click: it must NOT route off the finder, and it must NOT dismiss the floating card
      if (row) row.click();
      const detail = document.getElementById('vault-detail') as HTMLElement | null;
      return {
        hadRow: !!row,
        hadArt: !!art,
        tipOpenedOnHover,
        cardOpen: !!(detail && !detail.hidden),
        tipStillOpen: !!(tip && tip.classList.contains('on')),
      };
    });
    expect(r.hadRow, 'the finder lists the owned shared item').toBe(true);
    expect(r.hadArt, 'the FIND row carries the item art - the HD hover anchor').toBe(true);
    expect(r.tipOpenedOnHover, 'hovering the item art opens the floating HD card').toBe(true);
    // GREEN: the click stays on the vault. RED: _sharedSetPage opened the full Shared Stash page.
    expect(r.cardOpen, 'a FIND-row click opens no shared stash page - it stays on the vault (#79)').toBe(false);
    // GREEN: the card stays (v169 keep-open now carries .vfr-row). RED: the click dismissed it.
    expect(r.tipStillOpen, 'the floating HD card stays open on the click - keep-open (#79)').toBe(true);
  });
});
