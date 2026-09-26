import { test, expect } from '@playwright/test';

// v327 — "Delete unsorted" button in the dock bar: wipes every UNSORTED item from owned,
// leaves items already filed in a mule untouched.
test('Delete-unsorted button clears the dock but keeps filed items', async ({ page }) => {
  page.on('dialog', d => d.accept());
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.evaluate(() => { (window as any).uiConfirm = () => Promise.resolve(true); }).catch(() => {});
  await page.waitForFunction(() => (window as any).vaultClearUnsorted && (window as any).suggestMule);
  await page.evaluate(() => { (window as any).switchTab && (window as any).switchTab('tools'); });
  const r = await page.evaluate(async () => {
    const owned = (window as any).eval('owned');
    owned.add('Chance Guards');               // will get auto-filed
    owned.add('Socketed Body Armor');         // will get auto-filed
    owned.add('Death Cleaver');               // leave UNSORTED
    (window as any).renderVault();
    // file two, leave Death Cleaver unsorted
    // #246 — the sorter files WITNESSES only, so the two are filed through the one door with a stash
    // witness (two independent looks, each with its own frame and conf); the router picks their mule
    const LOOKS = [{ session: 's_a', frame: 'f_a.jpg', conf: 0.9 }, { session: 's_b', frame: 'f_b.jpg', conf: 0.85 }];
    ['Chance Guards', 'Socketed Body Armor'].forEach((n) => (window as any).vaultFile(n, { lane: 'stash', sessions: LOOKS }));
    (window as any).vaultAutoAssign();
    const assignAfterSort = JSON.parse(localStorage.getItem('d2r_muleAssign')||'{}');
    // un-file Death Cleaver so it's unsorted again (it auto-filed too); simulate an unsorted leftover
    // instead: add a fresh unsorted item that has a home but we DON'T assign
    owned.add('Bonesnap');                    // unsorted (not auto-assigned this pass)
    (window as any).renderVault();
    const barHasClear = !!document.querySelector('#vault-dock-bar .vault-clear-btn');
    const dockBefore = document.querySelectorAll('#vault-dock .vault-chip').length;
    await (window as any).vaultClearUnsorted();   // v341.60 — async (awaits uiConfirm); await before reading the dock
    const dockAfter = document.querySelectorAll('#vault-dock .vault-chip').length;
    const stillOwnedFiled = (window as any).eval('owned').has('Chance Guards');
    const unsortedGone = !(window as any).eval('owned').has('Bonesnap');
    return { barHasClear, dockBefore, dockAfter, stillOwnedFiled, unsortedGone };
  });
  expect(r.barHasClear).toBe(true);
  expect(r.dockBefore).toBeGreaterThan(0);
  expect(r.dockAfter).toBe(0);            // dock emptied
  expect(r.stillOwnedFiled).toBe(true);   // filed item kept
  expect(r.unsortedGone).toBe(true);      // unsorted item deleted from owned
});
