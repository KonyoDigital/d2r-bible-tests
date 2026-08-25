import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v2099 finished the board half of this file and left a written promise: "⚠ COVERAGE MOVED AND IS
   NOT YET REPLACED on the console side." This is that replacement, so the console harness lives
   here now. Copied from tests/v1614_game_art_icons.spec.ts — every route FULFILLS, because an
   abort surfaces as a console error the console's own specs then red on. */
const ORIGIN = 'http://tvd.console.test';
const REPO = path.resolve(__dirname, '..');
const UI = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');

/* `URL` above is this file's board path, a STRING, so `new URL(...)` here would call a string —
   the global constructor is shadowed in the value namespace (the type annotations below still
   resolve to the DOM interface, which lives in a different namespace). The origin is fixed and
   ours, so the path is taken off the front of it rather than parsed. */
const pathOf = (u: string) => u.slice(ORIGIN.length).split('?')[0].split('#')[0];

async function console_(page: any) {
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname.startsWith('/art/'), (r: any) => {
    const p = path.join(REPO, pathOf(r.request().url()).replace(/^\//, ''));
    return fs.existsSync(p)
      ? r.fulfill({ status: 200, contentType: 'image/png', body: fs.readFileSync(p) })
      : r.fulfill({ status: 404, contentType: 'text/plain', body: '' });
  });
  await page.route((u: URL) => u.pathname.startsWith('/api/'),
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
}

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
 *
 * ⚠ THE SAY-STRINGS ABOVE ARE STILL THE ROUTE'S (control_app.py _shadow_state), but AMBER was the
 * BOARD widget's colour and that widget is gone. v2085/v2093/v2097 moved the switch into the
 * console's ⚙ ADVANCED drawer, which spells the same three states in the platform's own
 * vocabulary instead of bespoke classes: aria-pressed="true" is ON, plain is OFF, [disabled] is a
 * lane that cannot run — dimmed to .5 rather than tinted (tv/control_ui.html:4331-4335).
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
     DEAD differently from OFF, or "switched off" and "cannot run" look identical.

     v2101 — MEASURED IN THE DOCUMENT THAT OWNS THE SWITCH. This asked bible.html for `.sha-on` and
     `.sha-dead`, and v2097 deleted that row, its four painters and its 27 CSS rules when the
     shadow reader moved to the console's ⚙ ADVANCED drawer — Konyo asked for that twice. Both
     class names are now ZERO occurrences in bible.html, so the check could only be red, and
     pinning it back to the board would be asserting a copy he explicitly did not want.
     The console spells the three states with the platform's own vocabulary rather than bespoke
     classes: aria-pressed="true" is ON, plain is OFF, [disabled] is a lane that cannot run
     (tv/control_ui.html:4331-4335). So the states are DRIVEN and their painted result compared —
     a class name is not an appearance, and this now fails on a look, not on a spelling. */
  await console_(page);
  const r = await page.evaluate(() => {
    const sw: any = document.getElementById('sadv-sha');
    if (!sw) return { missing: true };
    // the drawer is a closed <details>; open it so the switch is laid out, not merely styled
    const det = sw.closest('details');
    if (det) det.open = true;
    const dot: any = sw.querySelector('.shadow-adv-dot');
    const look = () => ({
      opacity: getComputedStyle(sw).opacity,
      border: getComputedStyle(sw).borderTopColor,
      background: getComputedStyle(sw).backgroundColor,
      dot: dot ? getComputedStyle(dot).backgroundColor : null,
    });
    sw.removeAttribute('disabled'); sw.setAttribute('aria-pressed', 'false');
    const off = look();
    sw.setAttribute('aria-pressed', 'true');
    const on = look();
    sw.setAttribute('aria-pressed', 'false'); sw.setAttribute('disabled', '');
    const dead = look();
    sw.removeAttribute('disabled');
    return { missing: false, off, on, dead, hasDot: !!dot,
             box: sw.getBoundingClientRect().height };
  });
  expect(r.missing, 'the ⚙ ADVANCED drawer has no #sadv-sha switch — the shadow reader has no door').toBe(false);
  expect(r.hasDot, 'the switch carries no .shadow-adv-dot lamp to read a state off').toBe(true);
  expect(r.box, 'the switch has no box — it cannot show a state nobody can see').toBeGreaterThan(0);
  const key = (s: any) => JSON.stringify(s);
  expect(key(r.on), `ON and OFF paint identically (${key(r.on)}) — his choice has no appearance`)
    .not.toBe(key(r.off));
  expect(key(r.dead), `DEAD and OFF paint identically (${key(r.dead)}) — a lane that CANNOT run `
    + 'looks exactly like one he switched off, which is the g5 scar verbatim').not.toBe(key(r.off));
  expect(key(r.dead), 'DEAD and ON paint identically — the worst of the three to confuse')
    .not.toBe(key(r.on));
  expect(new Set([key(r.off), key(r.on), key(r.dead)]).size, 'three facts, three appearances').toBe(3);
});
