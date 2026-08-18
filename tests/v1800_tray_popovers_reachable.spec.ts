import { test, expect } from './_net_stub';
import * as path from 'path';

// v1800 — A CONTROL THAT RENDERS AND CANNOT BE CLICKED.
//
// The tray popovers (.tools-legend-pop, .forge-legend-pop, .inbox-pop) are bottom-anchored at
// calc(var(--dock-h) + N) and grow UPWARD. Three separate ways that put a control out of reach,
// all measured on this file rather than reasoned about:
//
//   1. THE HEIGHT. At 1440x800 .tools-legend-pop budgeted 74vh against a viewport that could not
//      hold it and rendered at top:-42px — its heading off the top of the screen, unreachable,
//      because overflow:auto scrolls content inside a box whose own top is already gone. Fixing
//      .inbox-pop alone (v1799) left this sibling and .forge-legend-pop running.
//
//   2. THE ANCHOR. Below ~620px tall the anchor ITSELF is the defect: a box pinned at dock+118
//      cannot fit above itself on a 400px viewport at any height. There the popovers flip to
//      top-anchored, which is the only arrangement that keeps the heading on screen.
//
//   3. THE STACK. #claim-bar is position:sticky, z-index:9997; the popovers are z-index:9001. So
//      with the bar up, document.elementFromPoint over the popover's OWN ✕ returned #claim-bar:
//      the close button was rendered, styled, pointer-events:auto — and dead. Nothing about the
//      pixels says so, which is why this is pinned by a HIT TEST and not by a screenshot or a
//      geometry assertion. A test that only measured rectangles would have passed all three.
//
// The claim bar's height is measured live into --claim-h (it wraps to 96/128/147/167px as the
// viewport narrows) for the same reason --chrome-top stopped being a hardcoded 70px in v708.1: a
// guessed constant is wrong the moment the thing it stands for reflows.

const FILE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

const SIZES = [
  { w: 1440, h: 900 },
  { w: 1440, h: 800 },   // where .tools-legend-pop measured top:-42
  { w: 901,  h: 700 },
  { w: 640,  h: 400 },   // below the 620px flip, and where the honest remainder is 51px
  { w: 375,  h: 700 },
];

for (const claimBarUp of [false, true]) {
  for (const { w, h } of SIZES) {
    test(`v1800 tools legend popover is reachable at ${w}x${h} (claim bar ${claimBarUp ? 'up' : 'dismissed'})`, async ({ page }) => {
      await page.setViewportSize({ width: w, height: h });
      await page.goto(FILE);
      // claim the browser (or un-claim it) BEFORE the load that matters — the bar decides at init
      await page.evaluate((up) => {
        if (up) localStorage.removeItem('d2r_ownerClaim');
        else localStorage.setItem('d2r_ownerClaim', '*');
      }, claimBarUp);
      await page.goto(FILE);
      await page.click('[data-tab="tools"]');
      await page.waitForTimeout(400);
      await page.click('.tools-legend-fab');
      await page.waitForTimeout(400);

      const m = await page.evaluate(() => {
        const p = document.querySelector('.tools-legend-pop') as HTMLElement;
        if (!p) return null;
        const x = p.firstElementChild as HTMLElement;
        const r = x.getBoundingClientRect();
        const hit = document.elementFromPoint(Math.round(r.left + r.width / 2),
                                              Math.round(r.top + r.height / 2));
        const pr = p.getBoundingClientRect();
        return {
          top: Math.round(pr.top), bottom: Math.round(pr.bottom), height: Math.round(pr.height),
          closeReachable: hit === x || x.contains(hit as Node),
          hitWas: hit ? ((hit as HTMLElement).id || (hit as HTMLElement).className || hit.tagName).toString() : 'none',
          vh: window.innerHeight,
        };
      });

      expect(m, 'the tools legend popover did not open').not.toBeNull();
      // (1) and (2): the panel's own top is on screen
      expect(m!.top, `popover top ${m!.top} is above the viewport — its heading is unreachable`).toBeGreaterThanOrEqual(0);
      expect(m!.bottom, `popover bottom ${m!.bottom} is below the ${m!.vh}px viewport`).toBeLessThanOrEqual(m!.vh);
      // a panel too short to read is a dead control even when its arithmetic is correct
      expect(m!.height, `popover collapsed to ${m!.height}px`).toBeGreaterThanOrEqual(150);
      // (3): the close button is not merely visible, it is HIT
      expect(m!.closeReachable,
        `the popover's close button is covered by ${m!.hitWas} — rendered, styled and unclickable`).toBe(true);
    });
  }
}
