// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';

// v363/v364 — the SHARED STASH fullscreen replica = D2R's 5 shared tabs. AUTO-SORT routes "worth keeping
// close" items (high/very-high trade value) → SHARED during intake (alongside muling the rest). The
// replica lays them on the tab for their SLOT (#264: weapons · armor/helms/shields · gloves/belts/boots ·
// rings/amulets/charms), best value first; tab 5 is spare looting room.

const URL = 'file://' + process.cwd() + '/bible.html';

test('high-value items auto-route to SHARED, laid on the tab for their slot (#264); tab 5 is spare', async ({ page }) => {
  const errs: string[] = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.addInitScript(() => {
    localStorage.setItem('d2r_owned', JSON.stringify(['Annihilus', 'Arachnid Mesh', 'Crown of Ages', 'Windforce', 'Axe of Fechmar']));
    localStorage.setItem('d2r_muleAssign', JSON.stringify({ Annihilus: 'shared', 'Arachnid Mesh': 'shared', 'Crown of Ages': 'shared', Windforce: 'uni-weap', 'Axe of Fechmar': 'uni-weap' }));
  });
  await page.setViewportSize({ width: 1500, height: 950 });
  await page.goto(URL);
  await page.waitForTimeout(1800);
  await page.evaluate(() => (window as any).switchTab('tools'));
  const r = await page.evaluate(() => {
    const w = window as any;
    // v409: Annihilus / Torch / Gheed's are NEVER-MULE keepers (__keep — kept on your active character), so the
    // "high value auto-routes to SHARED" rule is verified with a genuine high-value SHARED item (Arachnid Mesh).
    const routes = { anni: w.suggestMule('Annihilus').id, arachnid: w.suggestMule('Arachnid Mesh').id, wf: w.suggestMule('Windforce').id };
    w.openMuleCard('shared');
    const counts: number[] = [];
    for (let i = 0; i < 5; i++) { w._sharedSetPage(i); counts.push(document.querySelectorAll('#vault-detail .vd-item').length); }
    return { routes, counts };
  });
  expect(errs).toEqual([]);
  expect(r.routes.anni).toBe('__keep');        // never-mule keeper, not shared
  expect(r.routes.arachnid).toBe('shared');    // high trade value → auto-routes to SHARED
  expect(r.routes.wf).not.toBe('shared');
  // #264 (REG-2019) — the 5 tabs are laid out BY SLOT: Crown of Ages (a helm) on tab 2, Arachnid Mesh (a belt) on
  // tab 3, Annihilus (a charm) on tab 4; tab 1 holds weapons (none here) and tab 5 is the spare room
  expect(r.counts).toEqual([0, 1, 1, 1, 0]);
});
