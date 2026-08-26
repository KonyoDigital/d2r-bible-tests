import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v2177 — 455 PIXELS OF HIS CONSOLE WERE OFF THE RIGHT EDGE, AND NOTHING COULD SCROLL TO THEM.
//
// Measured on his LIVE console (http://127.0.0.1:17772) at the width control_app.py:3518 gives
// the window it creates — 1120:
//
//     .shell   grid-template-columns computed to   1286.77px 257.594px   = 1575px of page
//     html.scrollWidth 1120 == window.innerWidth 1120,   html/body overflow-x: hidden
//
//     TAB           left  right   on screen   reachable
//     F·Sets         858   1008      yes         yes
//     Tools         1012   1152      NO — half clipped
//     Vault         1156   1297      NO — entirely off screen
//     TV·D          1301   1432      NO — entirely off screen
//     RELAUNCH NOW  1114   1254      6 of its 140 pixels visible
//     ✕ (dismiss)   1264   1294      NO
//
// `scrollWidth === innerWidth` while content exists past it means GONE, not scrolled — the exact
// signature from [[visual-regression-detector]] ("four console buttons clipped and UNPRESSABLE").
// Vault is the vault manager. TV·D is the tab that runs the chronicle sweep. Both unreachable in
// the window the app opens by default.
//
// ONE CAUSE, EVERY SYMPTOM: `.shell` is `display:grid` with `grid-template-columns: 1fr clamp(...)`,
// and a bare `1fr` track carries an automatic minimum of MIN-CONTENT. The head area holds eight
// tabs, its min-content is 1287px, so the track refused to go below that and dragged the page open
// to 1575. Every stretched row inherited the blown-out width — which is why the fleet bar measured
// 1287 wide inside a 1120 window and pushed its own action button off the edge. `minmax(0, 1fr)`
// removes the floor and the whole page falls back inside the window.
//
// ⚠ THE FILE ALREADY KNEW. v1464, thirty lines below the fix, repairs the identical class at
// ≤900px and describes it in the same words: "31 elements stranded right-of-viewport, invisible
// and unreachable". It was fixed at one breakpoint and never swept to the template that governs
// every other width — including the only width his desktop window actually opens at.
// [[feedback-generalize-fixes]]
//
// ⚠ WHY THIS EXECUTES. The defect is invisible to every text and DOM assertion: the tabs are in
// the markup, they have their labels, their handlers are bound, `textContent` is perfect. Only
// GEOMETRY differs, and nobody had written a geometry assertion at 1120. [[grok-second-eye]]

const REPO = path.resolve(__dirname, '..');
const ORIGIN = 'https://bull-4-u.com/console';

/* v2177 — THE RED SWITCH. Point the spec at the PRE-FIX template and it must go red for the
   reason in the header, not for a missing selector. A gate never seen red is measuring nothing.
       V2177_OLD_TEMPLATE=1 npx playwright test tests/v2177_*.spec.ts
   [[feedback-blind-fixture-green-gate]] */
const OLD = !!process.env.V2177_OLD_TEMPLATE;

function ui(): string {
  let s = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');
  const FIXED = 'grid-template-columns: minmax(0, 1fr) clamp(238px, 23vw, 430px);';
  expect(s.includes(FIXED),
    'the .shell template is not the v2177 one — this spec is asserting against a shape that is '
    + 'no longer there, so it proves nothing').toBe(true);
  if (OLD) s = s.replace(FIXED, 'grid-template-columns: 1fr clamp(238px, 23vw, 430px);');
  return s;
}

async function mount(page: any, width: number) {
  const UI = ui();
  await page.setViewportSize({ width, height: 660 });   // 1120x660 is the window control_app opens
  await page.addInitScript(() => {
    localStorage.setItem('d2r_lsrRoute', JSON.stringify(
      { v: 2, owner: 'konyo', id: 'test-install', m: 'test-mac', p: '', pfx: '', lpfx: '', lp: '', wp: '' }));
  });
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname.startsWith('/art/'), (r: any) =>
    r.fulfill({ status: 200, contentType: 'image/png', body: '' }));
  await page.route((u: URL) => u.pathname.startsWith('/api/'), (r: any) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => document.body.setAttribute('data-view', 'sessions'));
  await page.waitForTimeout(1200);
}

/** Show the update bar with the message length he ACTUALLY gets, meter and all. A bar exercised
 *  with a short string is [[gate-blind-to-unexercised-input]] — the real one is 831px wide. */
async function showFleetBar(page: any) {
  await page.evaluate(() => {
    const bar = document.getElementById('fleet-bar') as HTMLElement;
    const txt = document.getElementById('fleet-txt') as HTMLElement;
    const eta = document.getElementById('fleet-eta') as HTMLElement;
    if (!bar || !txt) return;
    bar.hidden = false;
    txt.textContent = 'v2176 is on disk — this window is still running the old one. '
                    + 'Relaunch to use it.';
    if (eta) { eta.hidden = false; }
  });
  await page.waitForTimeout(300);
}

/* ⚠ THIS SPEC CANNOT REPRODUCE HIS DEFECT, AND SAYING SO IS THE POINT.
   With the pre-fix template restored, eight of nine assertions here still passed. Measured cause:
   in Playwright the console's tab strip renders 750px wide; on HIS machine it is 1223px (topbar
   1082 vs 1556). The blow-out only engages once the head content exceeds the track's fair share,
   so under the harness's narrower font metrics BOTH templates resolve to exactly
   "813.156px 257.594px" and a planted 1800px child moves neither. I wrote a stress test for that
   and deleted it: it was green on the broken tree at every width, which makes it a gate that
   cannot fail. [[feedback-blind-fixture-green-gate]]

   The evidence for the fix is therefore a CONTROLLED BEFORE/AFTER ON THE LIVE CONSOLE, one CSS
   declaration apart, in the same session at 1120px:

       1fr           -> tracks 1286.77px 257.594px, 455px past the edge, Vault+TV·D unreachable
       minmax(0,1fr) -> tracks  813.156px 257.594px,   0px past the edge, every tab reachable

   The deterministic half — no page-level grid track may be a bare `1fr` — is enforced where it
   can be enforced anywhere, by PARSING the stylesheet:
   tv/test_control.py :: TestV2177APageLevelGridTrackMustBeAbleToShrink.

   What these three assertions still buy: they go red the day the tab strip genuinely outgrows the
   window on CI's own fonts, and they are the record of what was measured. They are a floor, not
   the proof. */
for (const w of [1120, 901, 1440]) {
  test(`at ${w}px nothing in the console lives past the right edge`, async ({ page }) => {
    await mount(page, w);
    const m = await page.evaluate(() => ({
      inner: window.innerWidth,
      bodyScroll: document.body.scrollWidth,
      htmlScroll: document.documentElement.scrollWidth,
      htmlOverflowX: getComputedStyle(document.documentElement).overflowX,
      cols: getComputedStyle(document.querySelector('.shell') as Element).gridTemplateColumns,
    }));
    expect(m.bodyScroll, `${m.bodyScroll - m.inner}px of console exists past the right edge at `
      + `${w}px, and html.overflow-x is "${m.htmlOverflowX}" so NOTHING CAN SCROLL TO IT. `
      + `.shell grid-template-columns resolved to "${m.cols}" — a bare 1fr track cannot go below `
      + `its min-content, so the widest child drags the whole page open.`)
      .toBeLessThanOrEqual(m.inner + 1);
  });

  test(`at ${w}px every head tab is on screen and hit-tests to itself`, async ({ page }) => {
    await mount(page, w);
    const tabs = await page.evaluate(() => {
      const iw = window.innerWidth;
      return Array.from(document.querySelectorAll('.head-tabs .ht')).map((b) => {
        const r = (b as HTMLElement).getBoundingClientRect();
        const cx = Math.min(Math.max(r.left + r.width / 2, 1), iw - 2);
        const hit = document.elementFromPoint(cx, r.top + r.height / 2);
        return { label: (b.textContent || '').trim(),
                 right: Math.round(r.right), left: Math.round(r.left),
                 onScreen: r.right <= iw + 1 && r.left >= -1,
                 reachable: !!(hit && (hit === b || b.contains(hit))) };
      });
    });
    expect(tabs.length, 'no head tabs rendered — the harness never built the strip, so this spec '
      + 'would pass on a console with no navigation at all').toBeGreaterThanOrEqual(6);
    const off = tabs.filter((t) => !t.onScreen);
    expect(off, `these tabs are off the right edge at ${w}px and cannot be scrolled to: `
      + `${JSON.stringify(off)}. Vault is the vault manager and TV·D runs the chronicle sweep.`)
      .toEqual([]);
    const dead = tabs.filter((t) => !t.reachable);
    expect(dead, `these tabs are on screen but a click at their centre does not reach them at `
      + `${w}px: ${JSON.stringify(dead)} — something is painted over the tab strip`).toEqual([]);
  });

  test(`at ${w}px the update bar keeps its BUTTONS, and shrinks its prose instead`, async ({ page }) => {
    await mount(page, w);
    await showFleetBar(page);
    const b = await page.evaluate(() => {
      const iw = window.innerWidth;
      const bar = document.getElementById('fleet-bar') as HTMLElement;
      const go = bar.querySelector('.fb-go') as HTMLElement;
      const x = bar.querySelector('.fb-x') as HTMLElement;
      const txt = bar.querySelector('.fb-txt') as HTMLElement;
      const gr = go.getBoundingClientRect(), xr = x.getBoundingClientRect();
      return { inner: iw, barW: Math.round(bar.getBoundingClientRect().width),
               goVisiblePx: Math.round(Math.max(0, Math.min(gr.right, iw) - Math.max(gr.left, 0))),
               goTotalPx: Math.round(gr.width),
               xOn: xr.right <= iw + 1,
               txtEllipsised: txt.scrollWidth > txt.clientWidth + 1 };
    });
    // THE LAW: in a bar that can overflow, the ACTION is fixed and the PROSE gives way. He was
    // told "Relaunch to use it" while 134 of the button's 140 pixels sat outside his window —
    // which is why he said "i cant relaunch".
    expect(b.goVisiblePx, `RELAUNCH NOW has only ${b.goVisiblePx} of its ${b.goTotalPx} pixels on `
      + `screen at ${w}px (bar is ${b.barW}px wide in a ${b.inner}px window). The bar must shrink `
      + `its MESSAGE, never its button.`).toBe(b.goTotalPx);
    expect(b.xOn, `the dismiss ✕ is off screen at ${w}px, so a bar he cannot act on is also a bar `
      + `he cannot get rid of`).toBe(true);
  });
}
