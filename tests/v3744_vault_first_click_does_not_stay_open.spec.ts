// v3744 (REG-2245) — THE MULE WINDOW MUST NOT OUTLIVE ITS TAB.
//
// GrokBot, #230 tick 409 on his live console (v3614): "vault first click opened SHARED STASH, not
// the Vault body". #vault-detail is a body-level fixed overlay (.vd-fs, inset:0, z-index 99997)
// that openMuleCard appends to <body> and vaultCloseCard never moves back. A tab switch left
// `openMuleId` set and `box.hidden=false`, so the fullscreen card stayed stuck over whatever tab
// you landed on — and the console's shellOpen routes the board through switchTab (REG-1946), so
// once the SHARED card had been opened, routing the board back to the Vault showed that stuck card
// instead of the vault body.
//
// RED-first: drive the open -> switch sequence and assert the stale card is gone. BEFORE the fix,
// switchTab leaves #vault-detail visible (box.hidden stays false), so these are RED. Runs on GitHub
// CI only — never on his Mac.
import { test, expect } from './_net_stub';

const URL = 'file://' + process.cwd() + '/bible.html';

// open the SHARED STASH fullscreen card while standing on the Vault tab
async function openSharedOnVault(page: any) {
  return await page.evaluate(() => {
    const w = window as any;
    w.switchTab('vault');              // land on the Vault so the card's return-tab is the vault
    w.openMuleCard('shared');          // open the SHARED STASH fullscreen card
    const box = document.getElementById('vault-detail') as HTMLElement;
    return {
      open: !box.hidden && box.classList.contains('vd-fs'),
      locked: document.documentElement.classList.contains('vd-lock'),
    };
  });
}

function snapshot(page: any) {
  return page.evaluate(() => {
    const box = document.getElementById('vault-detail') as HTMLElement;
    const active = document.querySelector('.tab.active');
    return {
      hidden: !!box.hidden,
      fs: box.classList.contains('vd-fs'),
      mpOn: box.classList.contains('mp-on'),
      vdLock: document.documentElement.classList.contains('vd-lock'),
      activeTab: active ? active.getAttribute('data-tab') : null,
    };
  });
}

test('a mule card does not survive a programmatic tab switch (the console routes the board via switchTab)', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Arachnid Mesh']));
    localStorage.setItem('d2r_muleAssign', JSON.stringify({ 'Arachnid Mesh': 'shared' }));
  });
  await page.setViewportSize({ width: 1500, height: 950 });
  await page.goto(URL);
  await page.waitForTimeout(1800);

  const pre = await openSharedOnVault(page);
  expect(pre.open).toBe(true);     // precondition: the SHARED card is actually open fullscreen
  expect(pre.locked).toBe(true);   // and the board is locked behind it

  // route the board to another tab, exactly as the console's shellOpen does
  await page.evaluate(() => (window as any).switchTab('bosses'));
  const after = await snapshot(page);

  expect(errs).toEqual([]);
  expect(after.activeTab).toBe('bosses');   // the tab switch still happened — nothing was dropped
  expect(after.hidden).toBe(true);          // the stale card is gone
  expect(after.fs).toBe(false);
  expect(after.mpOn).toBe(false);
  expect(after.vdLock).toBe(false);

  // and routing back to the Vault shows the body, not the stuck card
  await page.evaluate(() => (window as any).switchTab('vault'));
  const back = await snapshot(page);
  expect(back.activeTab).toBe('vault');
  expect(back.hidden).toBe(true);
  expect(errs).toEqual([]);
});

test('a mule card does not survive a hash route (browser Back / a #deep-link)', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.setViewportSize({ width: 1500, height: 950 });
  await page.goto(URL);
  await page.waitForTimeout(1800);

  const pre = await openSharedOnVault(page);
  expect(pre.open).toBe(true);

  // a hashchange (Back/Forward, or a pasted #tab) routes through _v39_routeFromHash, which calls the
  // base switchTab directly — bypassing the switchTab wrapper — so the card must still close
  await page.evaluate(() => { location.hash = '#bosses'; });
  await page.waitForTimeout(250);
  const after = await snapshot(page);

  expect(errs).toEqual([]);
  expect(after.activeTab).toBe('bosses');
  expect(after.hidden).toBe(true);
  expect(after.fs).toBe(false);
  expect(after.vdLock).toBe(false);
});