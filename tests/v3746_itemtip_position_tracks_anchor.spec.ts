import { test, expect, seedOwnerRoute } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v3746 — THE CONSOLE'S STYLED TIP TRACKS ITS ANCHOR THROUGH A SCROLL, AND CLEARS WHEN THE POINTER
// LEAVES ITS HOST (REG-2252, ↩ #234).
//
// Two defects in one lane (`_itemTip` say / anchor), both pixel-and-position behaviour GrokBot
// photographed on the live console (ticks 383/400/402/404/407/435, consoles v3605–v3634):
//   (b) POSITION. The prose/row tip is ELEMENT-ANCHORED — anchor() reads node.getBoundingClientRect()
//       ONCE at show time. When the host is a chip/row inside the SCROLLED shelf overlay (the River
//       gallery's TRIAGE/SEAL chips, a fleet row, a held-film thumb), a wheel / PageDown / End scroll
//       fires 'scroll' but NO mouse event, so the rect went stale and the bubble hung far from its
//       anchor ("BEST COVERAGE" ~330px below its chip; the Shadow-reader tip painted over WHAT I
//       FOUND after a rail scroll). The fix re-glues a still-connected host to its CURRENT rect on
//       scroll, mirroring bible.html's arttip re-glue (v3742 REG-2240, bible.html:33135).
//   (a) LIFECYCLE. Every exit was about the POINTER (mousemove) or the WINDOW (scroll/blur/Esc/click);
//       none fired when the pointer simply left the host and then stayed put, so a tip outlived its
//       pointer on the TV-D HISTORY strip and a Wife-PC row tip painted over the rows beside it. The
//       fix adds a delegated mouseout on the tracked node, mirroring bible.html's arttip mouseout
//       (bible.html:33111).
//
// WHY A REAL-HOVER SPEC, not an internal call. A guard that drives anchor()/hide() directly can never
// go red for the document-level delegate that is supposed to call them on a real scroll / pointer-
// leave — the exact gap v2130 / v3744 named for this console. So this dispatches real events the
// shipped listeners handle, and measures #itip's painted rect, never an internal flag.
//
// RED-FIRST (reasoned, not run — browser specs run on GitHub CI, never on his Mac; see test-venue):
//   • Before the fix the scroll handler was `document.addEventListener('scroll', () => _itemTip.hide())`,
//     so a scroll HIDES the tip: `after.on` is false and the "offset stays constant" law cannot even
//     be measured — the tracking test fails at `expect(after.on).toBe(true)`.
//   • Before the fix there was NO mouseout handler, so the tip OUTLIVES the pointer leaving its host:
//     `cleared` (the tip is still .on after the mouseout) stays true — the clear test fails at
//     `expect(cleared).toBe(false)`.
// Both are pinned to the LAW (track the anchor / clear on leave), not to any pixel constant. The exact
// side-offset depends on his live WebKit metrics, so this asserts only that the anchor-to-tip offset
// stays ~constant across the scroll; render-verify the pixel landing on his console.

const ORIGIN = 'http://tvd.console.test';
const REPO = path.resolve(__dirname, '..');
const UI = fs.readFileSync(path.join(REPO, 'tv', 'control_ui.html'), 'utf8');

/** Load the console the proven way (v1617 / v3744): serve control_ui.html at a real http origin so
 *  its scripts run and the document-level mousemove/scroll/mouseout delegates bind. seedOwnerRoute
 *  gives it the route a real console always has; /api and /art are stubbed so load neither hangs nor
 *  errors. */
async function openConsole(page: any) {
  await seedOwnerRoute(page);
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname.startsWith('/art/'),
    (r: any) => r.fulfill({ status: 404, body: '' }));
  await page.route((u: URL) => u.pathname.startsWith('/api/'),
    (r: any) => r.fulfill({ status: 200, contentType: 'application/json', body: '{"ok":false}' }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  // wait on show() (present before AND after the fix), NOT on the new reglue() — the RED must land on
  // the behaviour assertions below, proving the LAW, not merely that a method name is now defined.
  await page.waitForFunction(() =>
    !!(window as any)._itemTip && typeof (window as any)._itemTip.show === 'function');
}

/** Build a scrollable overlay (the shelf's shape: an absolutely-positioned overflow:auto box) holding
 *  a titled row ANCHOR partway down its scroll content, and open the styled tip on it with a real
 *  mousemove — the same delegate path a live hover takes. Returns once #itip is painted. */
async function hoverAnchorInScroller(page: any) {
  await page.evaluate(() => {
    document.getElementById('_v3746box')?.remove();
    const box = document.createElement('div');
    box.id = '_v3746box';
    // position:fixed so the box's own viewport position is deterministic regardless of page scroll;
    // overflow:auto makes its CONTENT scroll (the shelf-overlay shape), moving the anchor in-viewport.
    box.style.cssText = 'position:fixed;top:140px;left:40px;width:280px;height:240px;overflow:auto;z-index:5;background:#101010';
    const inner = document.createElement('div');
    inner.style.cssText = 'position:relative;height:900px';
    const anchor = document.createElement('span');
    anchor.id = '_v3746anchor';
    anchor.textContent = 'BEST COVERAGE';
    anchor.setAttribute('title', 'BEST COVERAGE — open session 87');
    anchor.style.cssText = 'position:absolute;top:300px;left:20px;display:inline-block';
    inner.appendChild(anchor);
    box.appendChild(inner);
    document.body.appendChild(box);
    box.scrollTop = 180;                     // park the anchor mid-box (viewport y ~ 140 - 180 + 300 = 260)
    anchor.dispatchEvent(new MouseEvent('mousemove', { bubbles: true, clientX: 90, clientY: 260 }));
  });
  // say() opens on a cold-start ~380ms timer (longer than the item card); wait past it, plus the
  // open transition, before measuring.
  await page.waitForTimeout(600);
}

function tipAnchorTops(page: any) {
  return page.evaluate(() => {
    const tip = document.getElementById('itip');
    const anchor = document.getElementById('_v3746anchor') as HTMLElement;
    const tr = tip ? tip.getBoundingClientRect() : null;
    const ar = anchor.getBoundingClientRect();
    return {
      on: !!tip && tip.classList.contains('on'),
      tipTop: tr ? tr.top : NaN,
      anchorTop: ar.top,
    };
  });
}

test.describe('v3746 — the console styled tip tracks its anchor and clears on pointer-leave', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 1000 });
    await openConsole(page);
  });

  test('★★★ (b) the tip re-glues to its anchor when the shelf overlay scrolls under a still pointer', async ({ page }) => {
    await hoverAnchorInScroller(page);

    const before = await tipAnchorTops(page);
    // non-vacuity: the styled tip MUST actually open on the dispatched hover, or nothing below is a
    // measurement (v2130 / v3744's lesson — a lane that stopped binding would also be caught here).
    expect(before.on, 'the styled tip never opened on a real mousemove over a titled row — the lane '
      + 'did not bind or say() refused the node; nothing below proves anything if #itip is not up').toBe(true);
    const delta0 = before.tipTop - before.anchorTop;

    // scroll the OVERLAY (not the window): fires a capture-phase 'scroll' with no pointer event,
    // exactly like his WebKit wheel/PageDown case the render harness cannot feel.
    await page.evaluate(() => { (document.getElementById('_v3746box') as HTMLElement).scrollTop = 260; });
    await page.waitForTimeout(250); // let the scroll event fire and the handler re-glue

    const after = await tipAnchorTops(page);
    const delta1 = after.tipTop - after.anchorTop;

    expect(before.anchorTop - after.anchorTop, 'the anchor did not move in-viewport — the overlay '
      + 'never scrolled, so the test proves nothing').toBeGreaterThan(50);
    expect(after.on, 'a scroll blanked the tip instead of re-gluing it — this is the pre-fix '
      + 'behaviour (scroll -> hide), the exact thing #234 asked to stop').toBe(true);
    // THE LAW: the tip followed its anchor instead of hanging at its old screen position. Without the
    // re-glue, tipTop is frozen while anchorTop fell ~80px, so |delta1 - delta0| ~ 80; the re-glue
    // keeps the anchor-to-tip offset constant.
    expect(Math.abs(delta1 - delta0), 'the tip did not track its anchor through the scroll — it hung '
      + 'at a stale rect, landing far from the chip (GrokBot ticks 400/402/435)').toBeLessThan(24);
  });

  test('★★★ (a) the tip clears when the pointer leaves its host, with no further mouse move', async ({ page }) => {
    await hoverAnchorInScroller(page);

    const up = await tipAnchorTops(page);
    expect(up.on, 'the styled tip never opened, so a clear-on-leave assertion would be vacuous').toBe(true);

    // the pointer LEAVES the host onto bare chrome and then stays put: a single mouseout, no mousemove
    // after it. Pre-fix there is no mouseout handler, so the tip is stranded (GrokBot ticks 383/407).
    const cleared = await page.evaluate(() => {
      const anchor = document.getElementById('_v3746anchor') as HTMLElement;
      anchor.dispatchEvent(new MouseEvent('mouseout', { bubbles: true, relatedTarget: document.body }));
      const tip = document.getElementById('itip');
      return !!tip && tip.classList.contains('on');
    });

    expect(cleared, 'the tip outlived the pointer leaving its host — no mousemove followed to sweep '
      + 'it away, so it stayed painted over the rows beside it (the Wife-PC / held-film strandings)').toBe(false);
  });
});