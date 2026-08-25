import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v2000 — 👁 THE SHADOW READER GETS A SWITCH.
 *
 * Konyo: "is there a way to like have an AI lurking in the shadows reading the game ingame and
 * sometimes firing whats needed? … for this it should have an ON/OFF for shadow AI a button to
 * click a cool widget." Then, hunting Tools for it: "where exactly is ther button for SHADOW AI".
 *
 * There was none — measured, zero shadow-AI occurrences in bible.html, control_app.py and
 * tv_diablo.py. I had described the design and never built it, and he spent time clicking around
 * for a button that did not exist.
 *
 * The READER itself has existed since v932: tv_diablo's text eye OCRs the live frame and turns new
 * item-ish text into a PRIORITY read. What was missing was a switch he could reach. TV_TEXT_EYE is
 * read ONCE before the loop starts — a boot flag — and an env var of a running process cannot be
 * changed from outside anyway. The switch is now a file with exactly ONE writer (the console) and
 * ONE reader (the agent), checked inside the loop so it takes effect on the next 0.7s tick.
 *
 * THIS SPEC PINS THE OFF-CONSOLE HALF, which is what a file:// run can observe: the public site
 * must never poke a service on his laptop, so the widget stays HIDDEN rather than showing a toggle
 * that cannot do anything. The on-console states were verified against a stub on :17771 (never
 * :17772, his live console):
 *     armed -> "armed — it starts watching when a reel is rolling"      switch green
 *     live  -> "watching — it reads on-screen text and fires a priority read…"
 *     off   -> "the shadow reader is OFF — nothing is being watched"    switch grey
 *     dead  -> "no local OCR on this machine, so the lane cannot run…"  switch AMBER + disabled
 */

test('off-console the widget is hidden, never a toggle that cannot do anything', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const host = document.getElementById('shadow-ai');
    return {
      exists: !!host,
      hidden: host ? host.hidden : null,
      onConsole: w._shadowOnConsole ? w._shadowOnConsole() : null,
      render: typeof w.renderShadowAI,
      toggle: typeof w.toggleShadowAI,
    };
  });
  /* v2099 — INVERTED, because the product moved and this pinned the old shape. He asked twice for
     the shadow reader to live in ⚙ ADVANCED beside the Grok eyes; v2095 wired the drawer to the
     real orchestration and v2097 removed the board copies, their painters and 27 CSS rules. This
     required all of them, so it went red on the intended product — and, worse, it would have
     stayed GREEN if a second copy reappeared on the board, which is the exact drift that made him
     ask twice. Inverted it is strictly stronger. */
  expect(r.exists, '#shadow-ai is back on the board — two copies is how the last one hid').toBe(false);
  expect(r.render, 'renderShadowAI should be gone with its row').toBe('undefined');
  expect(r.toggle, 'toggleShadowAI should be gone with its row').toBe('undefined');
  expect(r.onConsole, 'a file:// page must not count as the console').toBe(false);
  // v2099 — `hidden` was read off the host; with the host gone it is null by construction, which
  // is the honest reading. Asserting `true` here would have been a check that can never pass.
  expect(r.hidden, 'there is no host left to be hidden — that is the point').toBeNull();
});

/* v2099 — TOMBSTONE: "toggling off-console does nothing and cannot throw" is REMOVED.
   It drove window.toggleShadowAI(), which v2097 deleted with the board row when the shadow reader
   moved to ⚙ ADVANCED — he asked for that twice. Its subject does not exist here any more, so the
   test could only ever be red.
   WHAT IT PROTECTED, and where it went: the drawer's shadow button POSTs /api/shadow and repaints
   from it; it never reached into the board. So "cannot throw off-console" is now a property of the
   CONSOLE, and a file:// spec of bible.html cannot see the console.
   ⚠ COVERAGE MOVED AND IS NOT YET REPLACED on the console side. Written down rather than dropped
   quietly: a deleted test nobody notices is how a capability goes dark. */

test('the three facts have three separate surfaces, not one lamp', async ({ page }) => {
  /* The G5 scar: one object answered "is it ready" and "was it asked" with the same word, and the
     lane sat dark for weeks with every lamp green. `on` is his choice, `available` is whether the
     lane can run at all, `recording` is whether a reel is rolling — the widget must be able to show
     DEAD differently from OFF, or "switched off" and "cannot run" look identical. */
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const css = await page.evaluate(() => {
    const sheets = Array.from(document.styleSheets) as CSSStyleSheet[];
    let txt = '';
    for (const s of sheets) {
      try { txt += Array.from(s.cssRules).map((r) => r.cssText).join('\n'); } catch (e) { /* cross-origin */ }
    }
    return txt;
  });
  expect(css, 'no .sha-on rule — ON has no distinct appearance').toContain('.sha-on');
  expect(css, 'no .sha-dead rule — a lane that CANNOT run would look identical to one switched off')
    .toContain('.sha-dead');
});
