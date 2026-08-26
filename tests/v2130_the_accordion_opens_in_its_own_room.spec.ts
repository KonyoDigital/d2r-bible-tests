import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v2130 — #95. THE ROOM-DEFAULT JOIN HAD NO SPEC, AND THE ONE SPEC NEARBY WENT VACUOUS.
//
// v2103 taught renderForge to default its `_scope` from the ACTIVE TAB, so an accordion opened
// while Crafts is the live room renders into #crafts-body rather than #forge-body. Nothing
// exercised it: the only two mentions of forgeCraftToggle in tests/ sit inside a COMMENT in
// v518 that still says the toggle "is currently broken in this room", and that spec opens the row
// through forgeSetFilter('crafts','crafts') instead — so reverting the join left everything green.
//
// This drives the REAL door: the function the accordion header's onclick calls.

test('opening a craft accordion in Crafts fills the Crafts body, not the Forge body', async ({ page }) => {
  await page.goto(URL);
  await page.waitForFunction(() => typeof (window as any).forgeCraftToggle === 'function'
                                && typeof (window as any).switchTab === 'function');

  const r = await page.evaluate(() => {
    const w = window as any;
    w.switchTab('crafts');

    /* v2134 — CLICK THE HEADER, do not call the function. Calling forgeCraftToggle directly skips
       the accordion header's own onclick, so removing that wiring — the thing he actually presses —
       would leave this spec green. The header is `.f-craftacc-h[role=button]`; there are four, one
       per craft type. Verified on the live board: clicking the first takes #crafts-body 0 -> 9 rows
       while #forge-body stays at 0. */
    const head = document.querySelector('#tab-crafts .f-craftacc-h') as HTMLElement | null;
    if (!head) return { err: 'no .f-craftacc-h in #tab-crafts — the accordion header he presses is '
                             + 'gone, so nothing was measured' };

    const rows = (id: string) => document.querySelectorAll('#' + id + ' .f-craftrow').length;
    const before = { crafts: rows('crafts-body'), forge: rows('forge-body') };
    head.click();
    const after = { crafts: rows('crafts-body'), forge: rows('forge-body') };
    return {
      key: (head.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40),
      before, after,
      room: (document.querySelector('.tab.active') as HTMLElement | null)?.getAttribute('data-tab'),
    };
  });

  expect(r.err, r.err || '').toBeUndefined();
  expect(r.room, 'switchTab("crafts") did not open the Crafts room, so this never reached its '
    + 'subject').toBe('crafts');
  expect(r.after!.crafts, 'the accordion opened and #crafts-body gained no recipe row — the room '
    + 'default did not take, which is exactly what v2103 fixed')
    .toBeGreaterThan(r.before!.crafts);
  expect(r.after!.forge, 'the accordion rendered into #forge-body while the CRAFTS room was live — '
    + 'the rows land in a pane he is not looking at').toBe(r.before!.forge);
});

test('the toggle does not blindly fill Crafts from another room either', async ({ page }) => {
  // THE MIRROR — and it is deliberately NOT "the Forge body fills too". MEASURED on the live
  // board: with Forge as the active room, toggling a craft renders NOTHING anywhere
  //     crafts-body 0 -> 9, forge-body 0 -> 0   (in Crafts)
  //     forge-body  0 -> 0                      (in Forge)
  // which is correct BY DESIGN — v2094 split crafts into their own room and v2096 took the ⚗️ chip
  // out of Forge, so Forge has no craft rows to render. Asserting that Forge fills would have made
  // this spec red for a decision that was made on purpose.
  //
  // What the mirror has to rule out is the opposite failure: a room default that ignores the room
  // and always writes into #crafts-body. So: stand in FORGE, toggle, and require that Crafts does
  // NOT quietly grow behind his back.
  await page.goto(URL);
  await page.waitForFunction(() => typeof (window as any).forgeCraftToggle === 'function'
                                && typeof (window as any).switchTab === 'function');

  const r = await page.evaluate(() => {
    const w = window as any;
    w.switchTab('forge');
    const key = (typeof w.CRAFTS !== 'undefined' && w.CRAFTS && w.CRAFTS[0])
      ? (w.CRAFTS[0].k || w.CRAFTS[0].key || w.CRAFTS[0].name) : null;
    if (!key) return { err: 'no craft type to open' };
    const rows = (id: string) => document.querySelectorAll('#' + id + ' .f-craftrow').length;
    const before = rows('crafts-body');
    w.forgeCraftToggle(key);   // the FUNCTION here on purpose: Forge renders no accordion header
    return { key, before, after: rows('crafts-body'),
             room: (document.querySelector('.tab.active') as HTMLElement | null)?.getAttribute('data-tab') };
  });

  expect(r.err, r.err || '').toBeUndefined();
  expect(r.room, 'switchTab("forge") did not open the Forge room').toBe('forge');
  expect(r.after!, 'toggling a craft from the FORGE room grew #crafts-body — the room default is '
    + 'not reading the room at all, it is just always writing to Crafts').toBe(r.before!);
});
