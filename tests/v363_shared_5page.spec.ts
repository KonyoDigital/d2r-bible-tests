// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';

// v363/v364 — the SHARED STASH fullscreen replica = D2R's 5 shared tabs. AUTO-SORT routes "worth keeping
// close" items (high/very-high trade value) → SHARED during intake (alongside muling the rest).
// #144.10 shared half (REG-2801, his ruling 2026-10-28: "the war stash is basically the shared stash with those 5 pages +
// the extra war mules") — the replica lays them on its 5 PAGES in the order its move tasks fill them: page 1 first,
// biggest first, page 2 only once page 1 is full. #264's by-slot tabs are gone.

const URL = 'file://' + process.cwd() + '/bible.html';

test('high-value items auto-route to SHARED, laid on its 5 pages in the plan\'s fill order (page 1 first)', async ({ page }) => {
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
  expect(r.routes.anni).toBe('shared');        // REG-2241: torches and anni stay in shared
  expect(r.routes.arachnid).toBe('shared');    // high trade value → auto-routes to SHARED
  expect(r.routes.wf).not.toBe('shared');
  // REG-2801 — three items fit page 1 with room to spare, so all three are on it and pages 2-5 are empty
  expect(r.counts).toEqual([3, 0, 0, 0, 0]);
});
