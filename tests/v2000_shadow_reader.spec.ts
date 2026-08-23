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
  expect(r.exists, 'the shadow widget markup is gone').toBe(true);
  expect(r.render, 'renderShadowAI is missing — the widget can never paint').toBe('function');
  expect(r.toggle, 'toggleShadowAI is missing — the switch is decoration').toBe('function');
  expect(r.onConsole, 'a file:// page must not count as the console').toBe(false);
  expect(r.hidden, 'the widget must stay hidden off-console, not show a dead switch').toBe(true);
});

test('toggling off-console does nothing and cannot throw', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const out = await page.evaluate(async () => {
    const w: any = window;
    const before = (document.getElementById('sha-sw') || { className: '' }).className;
    const r = await w.toggleShadowAI();
    return { r, after: (document.getElementById('sha-sw') || { className: '' }).className, before };
  });
  expect(out.r).toBeNull();
  expect(out.after).toBe(out.before);
});

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
