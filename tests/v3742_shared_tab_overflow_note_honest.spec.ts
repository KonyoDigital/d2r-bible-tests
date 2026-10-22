// REG-2240 (#137) — THE SHARED-TAB OVERFLOW NOTE MUST TELL THE TRUTH.
// A shared stash tab is 10×10 = 100 cells — the SAME size as the in-game tab. When a tab is full,
// extra items land in packed.left. The old note read "D2R shared tabs hold 100 slots; this is the
// 10×10 preview", implying the real stash is bigger than the preview and the overflow is only a
// drawing limit. It is not: an item that overflows the 10×10 preview overflows the real tab too,
// and there is no auto-spill to another tab or a mule. _sharedOverflowNote (pure, window-exported)
// now builds the note so this guard can reach it — it used to live inline where no test could.
import { test, expect } from './_net_stub';

const URL = 'file://' + process.cwd() + '/bible.html';

/* V0 spec refresh (#176) — the fixture was 120 'Zdummy' names filed to SHARED, piled on tab 5. Those names are no
   item, and the board draws only items it knows (_vaultKeeps, the ownedPool rule — the names stay in d2r_owned and
   in the stored d2r_muleAssign): measured on the merged V1 tree, owned held 120 but ownedPool() 0 and the shared
   stash 0, so tab 5 painted an empty grid (GrokBot V0: placed = 0) — the fixture, not the note, went missing. The
   v3742 page that wrote this spec measures the same (0 placed), so PART B was red from the day it was written; it
   is not a regression. It is rebuilt from REAL items: fifteen 2×3 / 2×4 weapon uniques filed to the shared stash. Every
   one has a slot on record (_sharedTabOf → tab 1, Weapons) and a measured footprint, so they cannot all fit one
   10×10 tab (≥ 120 cells; ten 2×4s fill it). Measured: tab 1 places 10, and the overflow note names the other 5.
   (No roster unique lands on tab 5 any more — every one has a slot — so the overflow is shown where it happens.) */
const WEAPONS = ['Windforce', 'Buriza-Do Kyanon', 'Goldstrike Arch', 'The Grandfather', 'Tomb Reaver', 'Bonehew',
  'Bloodtree Stump', 'Bonesnap', 'Cliffkiller', 'Eaglehorn', 'Hone Sundan', 'Kuko Shakaku', 'Spire of Honor',
  'Stoneraven', 'Woestave'];

test('shared-tab overflow note is honest: no "preview", names the items, says there is no spill', async ({ page }) => {
  await page.addInitScript((names: string[]) => {
    const assign: Record<string, string> = {};
    names.forEach((n) => { assign[n] = 'shared'; });
    localStorage.setItem('d2r_owned', JSON.stringify(names));
    localStorage.setItem('d2r_muleAssign', JSON.stringify(assign));
  }, WEAPONS);
  await page.setViewportSize({ width: 1500, height: 950 });
  await page.goto(URL);
  await page.waitForTimeout(1800);

  // PART A — the pure note builder (bulletproof RED-first: undefined before the fix, no DOM needed).
  const unit = await page.evaluate(() => {
    const w = window as any;
    const fn = w._sharedOverflowNote;
    if (typeof fn !== 'function') return { ok: false, empty: '', note: '' };
    return { ok: true, empty: String(fn([])), note: String(fn([{ n: 'Exile' }, { n: 'Grief' }])) };
  });
  expect(unit.ok).toBe(true);                                 // function exists + exported
  expect(unit.empty).toBe('');                                // nothing overflows → no note
  expect(unit.note).toContain('Exile');                       // names the overflow items
  expect(unit.note).toContain('Grief');
  expect(unit.note.toLowerCase()).not.toContain('preview');   // the misleading word is gone
  expect(unit.note).toContain('will not fit');                // honest headline
  expect(unit.note).toContain('no overflow spill');           // says the stash cannot spill on its own

  // PART B — the note is WIRED into the live render (the-unjoined-end), read synchronously (no re-render race).
  const rendered = await page.evaluate((names: string[]) => {
    const w = window as any;
    w.switchTab('tools');
    const tabs = names.map((n) => w._sharedTabOf(n).tab);
    w.openMuleCard('shared');
    w._sharedSetPage(0);   // tab 1, Weapons — where the fifteen weapons are laid by slot
    const placed = document.querySelectorAll('#vault-detail .vd-item').length;
    const ov = document.querySelector('#vault-detail .vd-overflow');
    const text = ov ? (ov.textContent || '') : '';
    return { tabs, placed, has: !!ov, text, named: names.filter((n) => text.indexOf(n) >= 0).length };
  }, WEAPONS);
  expect(new Set(rendered.tabs), 'PREMISE: every fixture weapon is laid on tab 1 (Weapons)').toEqual(new Set([0]));
  expect(rendered.placed).toBeGreaterThan(0);                     // the tab rendered its grid (render did not throw)
  expect(rendered.has).toBe(true);                                // and it overflowed
  expect(rendered.text.toLowerCase()).not.toContain('preview');   // honest in the real DOM
  expect(rendered.text).toContain('will not fit');
  expect(rendered.named, 'the live note names the items that did not fit').toBeGreaterThan(0);
});
