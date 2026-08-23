import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v2013 — 🔎 THE TOOLTIP PASS. Konyo: "or to click on what within the console? like we need a
 * feature button for this thats on/off cool desgined".
 *
 * WHAT IT IS FOR, measured by vault_doctor on his own film: 220 occupied cells across 10 stash
 * panels and ZERO readable names. D2R prints no names in a grid — a name exists only in the HOVER
 * TOOLTIP — so the whole chain starves on one thing only he can do.
 *
 * WHY A BUTTON. The three states already existed and had to be set SEPARATELY: arm the vault lane,
 * wake the shadow reader, start a reel. Three controls in two places, and getting one wrong makes
 * the pass silently worthless — the exact shape this board keeps auditing out.
 *
 * The on-console behaviour was proven against a stub on :17771 (never :17772, his live console):
 *     ok      -> "🔴 rolling — HOVER each item you want named."          switch amber, badge shown
 *     refused -> "lane armed and reader on, but the reel did not start: already recording…"
 * This spec pins what a file:// run can observe, and the parts that must hold everywhere.
 */

test('off-console it stays hidden — never a button that cannot do anything', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const w: any = window;
    const host = document.getElementById('tip-pass');
    return {
      exists: !!host,
      hidden: host ? host.hidden : null,
      toggle: typeof w.toggleTooltipPass,
      render: typeof w.renderTooltipPass,
      onConsole: w._shadowOnConsole ? w._shadowOnConsole() : null,
    };
  });
  expect(r.exists, 'the tooltip-pass markup is gone').toBe(true);
  expect(r.toggle, 'toggleTooltipPass is missing — the button is decoration').toBe('function');
  expect(r.render).toBe('function');
  expect(r.onConsole).toBe(false);
  expect(r.hidden, 'off-console it must hide, not show a dead switch').toBe(true);
});

test('toggling off-console changes nothing and cannot throw', async ({ page }) => {
  await page.goto(URL);
  await page.waitForTimeout(1500);
  const out = await page.evaluate(async () => {
    const w: any = window;
    const before = localStorage.getItem('d2r_tooltipPass');
    const r = await w.toggleTooltipPass();
    return { r, before, after: localStorage.getItem('d2r_tooltipPass') };
  });
  expect(out.r).toBeNull();
  expect(out.after).toBe(out.before);
});

test('the badge is a DELTA, not a total — zero after hovering is a real answer', async ({ page }) => {
  /* A total would read "247 owned" whether or not the pass captured anything, which is precisely
     the reading that hides a pass that did nothing. */
  await page.goto(URL);
  await page.waitForTimeout(1200);
  await page.evaluate(() => {
    localStorage.clear();
    localStorage.setItem('d2r_ownerClaim', '*');
  });
  await page.goto(URL);
  await page.waitForTimeout(1600);

  const r = await page.evaluate(() => {
    const w: any = window;
    // seed a vault that already has items, then start a pass: the badge must read 0, not 3
    w.LSR.setItem('d2r_owned', JSON.stringify(['Shako', 'Ist', 'Gheed’s Fortune']));
    w.LSR.setItem('d2r_tooltipPass', JSON.stringify({ on: true, baseline: 3, startedTs: 1 }));
    const host = document.getElementById('tip-pass')!;
    host.hidden = false;                       // render() would hide it off-console; we want the text
    w.renderTooltipPass();
    const zero = (document.getElementById('tp-count') || { textContent: '' }).textContent;
    // now two more names arrive, as a hover pass would produce
    w.LSR.setItem('d2r_owned', JSON.stringify(['Shako', 'Ist', 'Gheed’s Fortune', 'A', 'B']));
    w.renderTooltipPass();
    const two = (document.getElementById('tp-count') || { textContent: '' }).textContent;
    return { zero, two };
  });
  expect(r.zero, 'the badge counted the whole vault instead of the pass').toContain('0 named');
  expect(r.two, 'two names arrived and the badge did not move').toContain('2 named');
});

test('ending a pass reports what it yielded and does NOT stop the reel', async ({ page }) => {
  /* Sealing a recording is his ON AIR control. A toggle that silently stopped it would take a
     decision that is his, and lose the tail of a session he was still filming. */
  await page.goto(URL);
  await page.waitForTimeout(1200);
  await page.evaluate(() => { localStorage.clear(); localStorage.setItem('d2r_ownerClaim', '*'); });
  await page.goto(URL);
  await page.waitForTimeout(1600);

  const say = await page.evaluate(async () => {
    const w: any = window;
    w.LSR.setItem('d2r_owned', JSON.stringify(['a', 'b', 'c', 'd']));
    w.LSR.setItem('d2r_tooltipPass', JSON.stringify({ on: true, baseline: 1, startedTs: 1 }));
    // force the console check true for this call only
    const real = w._shadowOnConsole;
    w._shadowOnConsole = () => true;
    await w.toggleTooltipPass();
    w._shadowOnConsole = real;
    const st = JSON.parse(w.LSR.getItem('d2r_tooltipPass') || '{}');
    return { text: (document.getElementById('tp-say') || { textContent: '' }).textContent || '', st };
  });
  expect(say.st.on, 'the pass did not end').toBe(false);
  expect(say.st.last, 'the yield was not recorded').toBe(3);
  expect(say.text).toContain('3 item(s) named');
  expect(say.text.toLowerCase(), 'it must say the reel is still rolling, not silently seal it')
    .toContain('still rolling');
});
