import { test, expect } from '@playwright/test';

// v324 — socketed bases carry SOCKET COUNT + 1H/2H, items get D2 cell FOOTPRINTS (1x1..2x4),
// the vault renders them as a stash-style cell grid, and EXTRA_ITEMS now STICK to a mule
// (ownedPool no longer prunes them — the root bug behind "socketed items don't get a mule").

test.beforeEach(async ({ page }) => {
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => (window as any)._itemCells && (window as any).EXTRA_ITEMS && (window as any).extraItemDetailHtml);
});

test('socketed entries carry sockets + hand metadata', async ({ page }) => {
  const r = await page.evaluate(() => {
    const E = (window as any).EXTRA_ITEMS;
    return {
      ba4: E['Socketed Body Armor (4os)'],
      w1: E['Socketed 1H Weapon (5os)'],
      w2: E['Socketed 2H Weapon (4os)'],
    };
  });
  expect(r.ba4.sockets).toBe(4);
  expect(r.w1.sockets).toBe(5);
  expect(r.w1.hand).toBe('1h');
  expect(r.w2.sockets).toBe(4);
  expect(r.w2.hand).toBe('2h');
});

test('the detail card shows the socket count + handedness chip', async ({ page }) => {
  const html = await page.evaluate(() => (window as any).extraItemDetailHtml('Socketed 2H Weapon (6os)'));
  expect(html).toContain('gic-sock-chip');
  expect(html).toContain('6os');
  expect(html).toContain('2H');
  expect(html).toContain('Two-Handed'); // subtitle spells it out
});

test('the floating tooltip surfaces the socket count', async ({ page }) => {
  const html = await page.evaluate(() => (window as any)._extraTipHtml('Socketed 1H Weapon (4os)'));
  expect(html).toContain('4 sockets');
  expect(html).toContain('One-Handed');
});

test('_itemCells returns D2 footprints across the 1x1..8-cell range', async ({ page }) => {
  const r = await page.evaluate(() => {
    const f = (window as any)._itemCells;
    return {
      ring: f('The Stone of Jordan'),       // jewellery → 1x1
      armorSock: f('Socketed Body Armor'),   // explicit cells → 2x3
      twoH: f('Socketed 2H Weapon (6os)'),   // 2x4 = 8 cells
      helm: f('Socketed Helm (3os)'),        // 2x2
    };
  });
  expect(r.ring).toEqual({ w: 1, h: 1 });
  expect(r.armorSock).toEqual({ w: 2, h: 3 });
  expect(r.twoH).toEqual({ w: 2, h: 4 });
  expect(r.twoH.w * r.twoH.h).toBe(8);     // the "1-8x" ceiling
  expect(r.helm).toEqual({ w: 2, h: 2 });
});

test('EXTRA_ITEMS stick to a mule — ownedPool keeps them and renderVault does not prune the assignment', async ({ page }) => {
  await page.evaluate(() => { (window as any).switchTab && (window as any).switchTab('tools'); });
  const r = await page.evaluate(() => {
    // simulate an intake registering a socketed base, then run the real auto-assign flow
    (window as any).eval('owned').add('Socketed 2H Weapon (4os)');
    const sm = (window as any).suggestMule('Socketed 2H Weapon (4os)');
    (window as any).renderVault();                 // item should enter the unsorted dock (ownedPool fix)
    (window as any).vaultAutoAssign();              // route it to its mule via the module's in-memory assign
    (window as any).renderVault();                  // re-render: assignment must SURVIVE the prune
    const stillAssigned = JSON.parse(localStorage.getItem('d2r_muleAssign') || '{}')['Socketed 2H Weapon (4os)'];
    const tile = document.querySelector('.vm-cell[data-vault-item="Socketed 2H Weapon (4os)"]') as HTMLElement | null;
    return {
      mule: sm.id,
      stillAssigned,
      tilePresent: !!tile,
      span: tile ? tile.getAttribute('style') : null,
      osBadge: tile ? !!tile.querySelector('.vm-cell-os') : false,
    };
  });
  expect(r.mule).toBe('bases');
  expect(r.stillAssigned).toBe('bases');     // <- the v324 fix: was pruned before
  expect(r.tilePresent).toBe(true);
  expect(r.span).toContain('span 2');         // 2x4 footprint
  expect(r.osBadge).toBe(true);               // shows the 4os badge
});
