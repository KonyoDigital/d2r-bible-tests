// REG-2240 (#137) — THE SHARED-TAB OVERFLOW NOTE MUST TELL THE TRUTH.
// A shared stash tab is 10×10 = 100 cells — the SAME size as the in-game tab. When a tab is full,
// extra items land in packed.left. The old note read "D2R shared tabs hold 100 slots; this is the
// 10×10 preview", implying the real stash is bigger than the preview and the overflow is only a
// drawing limit. It is not: an item that overflows the 10×10 preview overflows the real tab too,
// and there is no auto-spill to another tab or a mule. _sharedOverflowNote (pure, window-exported)
// now builds the note so this guard can reach it — it used to live inline where no test could.
import { test, expect } from './_net_stub';

const URL = 'file://' + process.cwd() + '/bible.html';

test('shared-tab overflow note is honest: no "preview", names the items, says there is no spill', async ({ page }) => {
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
  const rendered = await page.evaluate(() => {
    const w = window as any;
    /* 2026-10-20 (REG-2320) — the fixture used to be 120 gibberish names ("Zdummy0"…) seeded as owned+shared. The
       load now drops names no catalogue knows, so the tab drew 0 items and the spec went red on its fixture, not
       on the note. 30 REAL weapon uniques (2x3 / 2x4 each, well past one 10x10 tab) filed to shared overflow the
       WEAPONS tab deterministically — every one has a known slot, so nothing depends on the spare tab's rules. */
    const WEAPONS = ["Windforce", "The Grandfather", "Doombringer", "The Reaper's Toll", "Tomb Reaver", "Eschuta's Temper",
      "Death's Web", "Lycander's Aim", "Titan's Revenge", "Thunderstroke", "Stormspire", "Hellslayer",
      "Messerschmidt's Reaver", "The Cranium Basher", "Ethereal Edge", "Djinn Slayer", "Bloodmoon", "Azurewrath",
      "Lightsabre", "Baranar's Star", "Schaefer's Hammer", "Earthshaker", "Cloudcrack", "Ribcracker", "Stone Crusher",
      "Boneslayer Blade", "Bonehew", "Buriza-Do Kyanon", "Eaglehorn", "Widowmaker"];
    WEAPONS.forEach((n) => { (eval('owned') as any).add(n); w.vaultAssign(n, 'shared'); });
    w.switchTab('tools');
    w.openMuleCard('shared');
    w._sharedSetPage(0);   // the weapons tab, where the 30 weapons overflow
    const placed = document.querySelectorAll('#vault-detail .vd-item').length;
    const ov = document.querySelector('#vault-detail .vd-overflow');
    return { placed, has: !!ov, text: ov ? (ov.textContent || '') : '' };
  });
  expect(rendered.placed).toBeGreaterThan(0);                     // the tab rendered its grid (render did not throw)
  expect(rendered.has).toBe(true);                                // and it overflowed
  expect(rendered.text.toLowerCase()).not.toContain('preview');   // honest in the real DOM
  expect(rendered.text).toContain('will not fit');
});
