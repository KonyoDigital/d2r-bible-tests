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
  // 120 slot-unknown dummies all routed to SHARED → they pile on tab 5 (spare) and overflow its 10×10.
  // Gibberish names resolve to no doll slot (tab 5) and to the default footprint, so overflow is
  // deterministic and does not depend on any item-size or routing table.
  await page.addInitScript(() => {
    const dummies: string[] = [];
    const assign: Record<string, string> = {};
    for (let i = 0; i < 120; i++) { const n = 'Zdummy' + i; dummies.push(n); assign[n] = 'shared'; }
    localStorage.setItem('d2r_owned', JSON.stringify(dummies));
    localStorage.setItem('d2r_muleAssign', JSON.stringify(assign));
  });
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
    w.switchTab('tools');
    w.openMuleCard('shared');
    w._sharedSetPage(4);   // the spare tab, where the slot-unknown dummies piled up
    const placed = document.querySelectorAll('#vault-detail .vd-item').length;
    const ov = document.querySelector('#vault-detail .vd-overflow');
    return { placed, has: !!ov, text: ov ? (ov.textContent || '') : '' };
  });
  expect(rendered.placed).toBeGreaterThan(0);                     // the tab rendered its grid (render did not throw)
  expect(rendered.has).toBe(true);                                // and it overflowed
  expect(rendered.text.toLowerCase()).not.toContain('preview');   // honest in the real DOM
  expect(rendered.text).toContain('will not fit');
});
