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
  /* v2099 — INVERTED, and it now pins the CAPABILITY rather than the row. v2097 removed the board
     row and its painter; ⚙ ADVANCED is this pass's only home. But toggleTooltipPass MUST live on:
     it arms the vault mini-lane, POSTs /api/shadow and POSTs /api/on — which STARTS A RECORDING —
     and tracks `startedReel` so OFF seals the reel IT started and never one HE started. That is a
     scar: a pass once recorded ~9GB/hour he never asked for. v2095 wired the drawer button to call
     exactly this function through the #tvd-eng iframe, so deleting it would silently drop the
     capability while every surface still looked wired. */
  expect(r.exists, '#tip-pass is back on the board — ⚙ ADVANCED is its only home').toBe(false);
  expect(r.toggle, 'toggleTooltipPass MUST survive — the drawer button calls it').toBe('function');
  expect(r.render, 'renderTooltipPass should be gone with its row').toBe('undefined');
  expect(r.onConsole).toBe(false);
  // v2099 — same: no host, so `hidden` is null rather than true.
  expect(r.hidden, 'there is no host left to be hidden — that is the point').toBeNull();
});

/* v2099 — TOMBSTONE: "toggling off-console changes nothing and cannot throw" is REMOVED — it read
   #tp-sw, deleted in v2097 with the row. The refusal itself still exists inside toggleTooltipPass
   (it returns early unless _shadowOnConsole()), and the spec above pins that the function survives
   at all, which is the part the drawer depends on. */

/* v2099 — TOMBSTONE: the badge test is REMOVED — it drove window.renderTooltipPass() and read
   #tp-count, both deleted in v2097 with the board row.
   WHAT IT PROTECTED: the badge counts only what THIS pass named, so a vault already holding 3
   items reads 0 rather than 3. That arithmetic did NOT go away — it lives in tooltipPassState()
   (`named: _tpOwnedCount() - st.baseline`), which the spec above now pins as surviving. What is
   gone is the painted badge that displayed it.
   ⚠ COVERAGE MOVED AND IS NOT YET REPLACED: the drawer shows the pass's status in #sadv-tip-say
   and no spec asserts that number yet. Recorded, not papered over. */

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
    // no startedReel: this pass did NOT start the reel, so the reel is HIS and must survive
    w.LSR.setItem('d2r_tooltipPass', JSON.stringify({ on: true, baseline: 1, startedTs: 1 }));
    // force the console check true for this call only
    const real = w._shadowOnConsole;
    w._shadowOnConsole = () => true;
    const verdict = await w.toggleTooltipPass();
    w._shadowOnConsole = real;
    const st = JSON.parse(w.LSR.getItem('d2r_tooltipPass') || '{}');
    return { verdict, st };
  });
  expect(say.st.on, 'the pass did not end').toBe(false);
  expect(say.st.last, 'the yield was not recorded').toBe(3);
  /* v2101 — READ THE VERDICT THE CALLER GETS, not #tp-say. v2097 deleted that element with the
     board row and rerouted every one of the pass's nine status lines to #sadv-tip-say on the
     PARENT document (bible.html:46833 _tpSay), because the button that runs the pass now lives in
     the console's ⚙ ADVANCED drawer. On a standalone file:// board window.parent === window, so
     _tpSay() returns null BY DESIGN and the old assertion was reading an element that cannot exist
     here — the same lookup-of-nothing the board's own guard forbids.
     The returned object is what the drawer actually consumes: v2095 wires the button as
     `Promise.resolve(toggleTooltipPass()).then(_shadowAdvRefresh)` (tv/control_ui.html:11313).
     Both halves of this test's law are in it — `named` is the yield, and `sealed:false` with
     `reelWasMine:false` IS "the reel is still rolling and it is yours". */
  expect(say.verdict, 'toggleTooltipPass returned nothing — the drawer has no verdict to paint').toBeTruthy();
  expect(say.verdict.named, 'the yield the caller is told about must match the store').toBe(3);
  expect(say.verdict.reelWasMine, 'a reel this pass did not start must be reported as HIS').toBe(false);
  expect(say.verdict.sealed, 'ending the pass must not seal a reel it did not start').toBe(false);
});

/* ⚠ COVERAGE GAP, RECORDED NOT PAPERED OVER — the WORDING of those nine lines is now painted into
   #sadv-tip-say on the console and no spec asserts it. The one that matters most is the branch
   above: "The reel is STILL ROLLING — you started it, so seal it from ON AIR when you are done."
   v2019 exists because the branch that fires when the news is worst was the branch that told him
   least, and the verdict fields asserted above prove the DECISION, not the sentence.
   Covering it needs a parent document that owns #sadv-tip-say with the board in a same-origin
   #tvd-eng frame — the console's real shape (tv/control_ui.html:13938 src="/board?app=1…") — which
   is a harness this file does not have yet. */
