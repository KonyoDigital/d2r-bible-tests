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

/* v1801 — THE POPOVERS ARE A LIST, because guarding one member is how this ship got here twice.
   The v1800 header enumerated all three and the body only ever opened .tools-legend-pop, so when
   the post-ship review found .inbox-pop rendering 28px tall at 640x400 — the HEADLINE defect of
   v1801 — the entire suite stayed green, and moving the @media block back above .inbox-pop would
   still leave it green. Its geometry is asserted nowhere else in the repo either. */
const POPOVERS = [
  { name: 'tools legend', tab: 'tools', fab: '.tools-legend-fab', pop: '.tools-legend-pop' },
  { name: 'inbox',        tab: 'tools', fab: '.inbox-fab',        pop: '.inbox-pop',
    // the inbox FAB only appears once the queue has something in it
    seed: true },
];

const SIZES = [
  { w: 1440, h: 900 },
  { w: 1440, h: 800 },   // where .tools-legend-pop measured top:-42
  { w: 901,  h: 700 },
  { w: 640,  h: 400 },   // below the 620px flip, and where the honest remainder is 51px
  { w: 375,  h: 700 },
];

for (const P of POPOVERS) {
for (const claimBarUp of [false, true]) {
  for (const { w, h } of SIZES) {
    test(`v1800 ${P.name} popover is reachable at ${w}x${h} (claim bar ${claimBarUp ? 'up' : 'dismissed'})`, async ({ page }) => {
      await page.setViewportSize({ width: w, height: h });
      await page.goto(FILE);
      // v1801 — RAISE THE BAR DIRECTLY. The first version of this spec toggled
      // localStorage.d2r_ownerClaim and re-loaded, which does NOTHING here: bible.html resolves
      // window._D2R_OWNER to true whenever navigator.webdriver && location.protocol==='file:'
      // ("AUTOMATION ONLY. An automated browser on a file:// copy is the test suite"), so the
      // claim-bar IIFE returns before it ever clears [hidden]. Both halves of the loop ran with
      // no bar, --claim-h stayed 0px, and five of the ten cases were exact duplicates of the
      // other five — a blind fixture inside the ship whose title is about a blind fixture. The
      // bar is now raised the way the page raises it, and ASSERTED up, so this can never quietly
      // become a no-op again. [[feedback-blind-fixture-green-gate]]
      // The inbox FAB only exists once the queue has rows, and seeding needs its own reload — so
      // the LAST navigation happens inside this block. v1804: the bar was previously raised and
      // asserted BEFORE that reload, on a page the inbox case then threw away, which means the
      // five inbox cases could silently drift back to measuring claim-bar-down geometry twice and
      // the assertion would still pass. The assertion now runs on the page the geometry is
      // actually measured on, which is the only page it says anything about.
      if (P.seed) {
        await page.evaluate(() => localStorage.setItem('d2r_chronicleInbox', JSON.stringify(
          ['Battlecage', 'Templar Coat', 'Toothrow', 'Shaftstop'].map((name) => ({ name, ts: 1755600000000 })))));
        await page.goto(FILE);
      }
      if (claimBarUp) {
        await page.evaluate(() => {
          const c = document.getElementById('claim-bar');
          if (c) { (c as HTMLElement).hidden = false; document.body.classList.add('has-claim-bar'); }
        });
        await page.waitForTimeout(300);
      }
      const barState = await page.evaluate(() => {
        const c = document.getElementById('claim-bar') as HTMLElement | null;
        return { up: !!(c && !c.hidden && c.getBoundingClientRect().height > 0),
                 claimH: getComputedStyle(document.documentElement).getPropertyValue('--claim-h').trim() };
      });
      expect(barState.up, `the claim bar is ${claimBarUp ? 'not up' : 'up'} — this case is not testing what it claims`).toBe(claimBarUp);
      if (claimBarUp) {
        expect(parseFloat(barState.claimH) > 0, `--claim-h is ${barState.claimH} with the bar up — the measurement never ran`).toBe(true);
      } else {
        expect(parseFloat(barState.claimH) === 0, `--claim-h is ${barState.claimH} with no bar — the popovers are giving up space for nothing`).toBe(true);
      }
      await page.click(`[data-tab="${P.tab}"]`);
      await page.waitForTimeout(400);
      await page.click(P.fab);
      await page.waitForTimeout(400);

      const m = await page.evaluate((SEL) => {
        const p = document.querySelector(SEL) as HTMLElement;
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
      }, P.pop);

      expect(m, `the ${P.name} popover did not open`).not.toBeNull();
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
}
