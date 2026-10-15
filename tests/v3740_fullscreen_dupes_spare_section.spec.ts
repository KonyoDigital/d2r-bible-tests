import { test, expect } from '@playwright/test';

// REG-2231 (#134 fullscreen follow-up) — the FULLSCREEN dupes window (openMuleCard('dupes')) now shows the shared
// overflow (the 3rd+ copies of a shared item) as display-only "spare" cells, mirroring the shelf card
// (v3738/REG-2226). His rule E: the shared stash keeps 2 copies; the rest are trade stock held in GRAIL-DUPES,
// thrown out NEVER. Self-contained: no _muleLoad packer change, the copies stay homed in 'shared', each spare cell
// carries no remove control, and the true total is the registered xN. No double-count: the shared view draws 2,
// the dupes window draws min(copies-2, _MULE_COPY_CAP).
//
// RED without the fix: window._vaultSharedOverflowHtml is undefined and the open dupes window has no .vmc-spare
// cells. GREEN: a 7-copy shared item draws 3 spare cells in the fullscreen dupes window (and the shelf agrees); a
// 2-copy item draws 0.

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    try {
      localStorage.setItem('d2r_ownerClaim', '*');
      localStorage.setItem('d2r_owned', JSON.stringify(['Grief', 'Raven Frost']));
      localStorage.setItem('d2r_copies', JSON.stringify({ 'Grief': 7, 'Raven Frost': 2 }));
      localStorage.setItem('d2r_muleAssign', JSON.stringify({ 'Grief': 'shared', 'Raven Frost': 'shared' }));
    } catch (e) {}
  });
  await page.goto('file://' + process.cwd() + '/bible.html');
  await page.waitForFunction(() => typeof (window as any).openMuleCard === 'function'
    && typeof (window as any).renderVault === 'function'
    && typeof (window as any)._vaultSharedOverflowCells === 'function');
});

test('the FULLSCREEN dupes window shows shared overflow (>2) as spare cells and agrees with the shelf (REG-2231)', async ({ page }) => {
  const r = await page.evaluate(() => {
    const W = window as any;

    // the overflow LOGIC (shared with the shelf): 7 copies -> min(7-2,3)=3 spare, 2 copies -> 0
    const logic = {
      grief: W._vaultSharedOverflowCells('Grief'),
      raven: W._vaultSharedOverflowCells('Raven Frost'),
    };

    // the single-source renderer must exist and build the section for the seeded overflow
    const hasHtmlHelper = typeof W._vaultSharedOverflowHtml === 'function';
    const html = hasHtmlHelper ? W._vaultSharedOverflowHtml() : '';

    // the SHELF card (v3738) — rendered so the drift guard can compare both surfaces
    W.renderVault();
    const shelf = document.querySelector('[data-vault-mule="dupes"]');
    const shelfSpares = shelf ? shelf.querySelectorAll('.vm-spare-sec .vmc-spare').length : -1;

    // the FULLSCREEN dupes window — the drill-down generic mule render
    W.openMuleCard('dupes');
    const box = document.getElementById('vault-detail');
    const open = !!box && !box.hidden;
    const winSpares = box ? box.querySelectorAll('.vm-spare-sec .vmc-spare').length : -1;
    const griefCells = box
      ? Array.from(box.querySelectorAll('.vm-spare-sec .vmc-spare'))
          .filter((c: any) => (c.getAttribute('data-arttip') || '').indexOf('Grief') >= 0).length
      : -1;
    const ravenCells = box
      ? Array.from(box.querySelectorAll('.vm-spare-sec .vmc-spare'))
          .filter((c: any) => (c.getAttribute('data-arttip') || '').indexOf('Raven Frost') >= 0).length
      : -1;
    // display-only: a spare cell must NOT carry a remove control (its home stays 'shared')
    const spareHasRemove = box
      ? Array.from(box.querySelectorAll('.vm-spare-sec .vmc-spare'))
          .some((c: any) => !!c.querySelector('.vm-cell-x'))
      : true;

    if (W.vaultCloseCard) W.vaultCloseCard();
    return { logic, hasHtmlHelper, htmlHasSpare: /vm-spare-sec/.test(html), shelfSpares, open, winSpares, griefCells, ravenCells, spareHasRemove };
  });

  // overflow math (the logic both surfaces share)
  expect(r.logic.grief).toBe(3);
  expect(r.logic.raven).toBe(0);
  // the single-source renderer exists and produces the section
  expect(r.hasHtmlHelper).toBe(true);
  expect(r.htmlHasSpare).toBe(true);
  // the fullscreen dupes window opened and drew exactly the 3 capped Grief spares, none for the 2-copy Raven Frost
  expect(r.open).toBe(true);
  expect(r.winSpares).toBe(3);
  expect(r.griefCells).toBe(3);
  expect(r.ravenCells).toBe(0);
  // DRIFT GUARD — the shelf card and the fullscreen window must show the SAME overflow
  expect(r.shelfSpares).toBe(3);
  expect(r.winSpares).toBe(r.shelfSpares);
  // display-only: a spare carries no remove control (nothing is re-filed off 'shared')
  expect(r.spareHasRemove).toBe(false);
});
