import { test, expect } from './_net_stub';
import * as path from 'path';

// v1810 — THE FLOATING TRAY RODE UP INTO THE TAB STRIP.
//
// The tray is a bottom-anchored COLUMN — help at calc(var(--dock-h) + 14px), the nav compass at
// +66, the forge legend at +118 — while the header and tab strip are top-anchored. On a tall
// window the two never meet, which is why this survived every gate: the render widths were
// 375/640/701/901/1440 and the HEIGHT was always whatever the runner defaulted to.
//
// Measured at 640x400 before the fix: the strip occupied y 240-271 and the 44px compass y 250-294,
// so the `session` tab hit-tested to #nav-fab and could not be clicked at all. At 844x390 — an
// iPhone in landscape, not a stress test — the HELP orb overlapped the strip by 42x44px, and at
// 640x400 it sat on #gsearch-input and clipped the placeholder.
//
// WHY THIS ASSERTS RECTANGLES AND NOT A HIT TEST, which is the opposite of what v1800 concluded.
// The strip scrolls horizontally, so WHICH tab is buried under an orb depends on scroll offset.
// Hit-testing found `session` blocked on one load and reported everything clear on the next, with
// no code change in between — a witness that appears and vanishes is not a guard. The invariant
// that holds at every scroll position: a fixed orb must not intersect the strip's BAND. If it
// does, some tab is unreachable at some offset. [[feedback-suspect-the-instrument]]
//
// PROVEN RED: with the @media (max-height:480px) rule defeated by a body-appended override, this
// reports overlaps at 844x390, 640x400 and 375x400, and stays clear at 640x481 and 1440x900 — so
// it fails for its own reason and the threshold acts only where it is meant to.

const FILE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

const ORBS = [
  { sel: '.help-btn',          name: 'S0 help' },
  { sel: '.nav-widget',        name: 'S1 compass' },
  { sel: '.forge-legend-fab',  name: 'S2 forge legend' },
];

const VICTIMS = [
  { sel: '.tabs',           name: 'tab strip' },
  { sel: '.tabs-workshop',  name: 'workshop row' },
  { sel: '#gsearch-input',  name: 'search field' },
];

// Short enough that the tray and the strip compete for the same band, plus two controls above the
// threshold to prove the rule does not reach where it should not.
const SIZES = [
  { w: 844, h: 390, short: true },   // iPhone landscape
  { w: 640, h: 400, short: true },   // the render gate's narrow width, at a short height
  { w: 375, h: 400, short: true },
  { w: 640, h: 481, short: false },  // one pixel above the threshold
  { w: 1440, h: 900, short: false },
];

for (const s of SIZES) {
  test(`v1810 — no tray orb intersects the tab strip or search at ${s.w}x${s.h}`, async ({ page }) => {
    await page.setViewportSize({ width: s.w, height: s.h });
    await page.goto(FILE);
    await page.waitForSelector('.tabs .tab', { state: 'attached' });
    await page.waitForFunction(() => {
      const v = getComputedStyle(document.documentElement).getPropertyValue('--dock-h').trim();
      return v !== '' && v !== '0px';
    }, null, { timeout: 15000 });

    const overlaps = await page.evaluate(({ orbs, victims }) => {
      const hits: string[] = [];
      for (const o of orbs) {
        const e = document.querySelector(o.sel) as HTMLElement | null;
        if (!e) continue;
        const cs = getComputedStyle(e);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        const a = e.getBoundingClientRect();
        if (a.width < 2) continue;
        for (const v of victims) {
          const t = document.querySelector(v.sel) as HTMLElement | null;
          if (!t) continue;
          if (getComputedStyle(t).display === 'none') continue;
          const b = t.getBoundingClientRect();
          if (b.width < 2 || b.height < 2) continue;
          const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left);
          const oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
          if (ox > 0 && oy > 0) {
            hits.push(`${o.name} x ${v.name} (${Math.round(ox)}x${Math.round(oy)}px)`);
          }
        }
      }
      return hits;
    }, { orbs: ORBS, victims: VICTIMS });

    expect(overlaps, `tray overlaps at ${s.w}x${s.h}`).toEqual([]);
  });
}

test('v1810 — above the threshold the tray is still THERE', async ({ page }) => {
  // The fix hides chrome. A rule that hid the tray everywhere would satisfy every assertion above
  // and quietly delete three controls — so the threshold gets its own witness on the other side.
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(FILE);
  await page.waitForSelector('.help-btn', { state: 'attached' });
  for (const sel of ['.help-btn', '.nav-widget']) {
    const shown = await page.evaluate((s) => {
      const e = document.querySelector(s) as HTMLElement | null;
      if (!e) return 'absent';
      return getComputedStyle(e).display;
    }, sel);
    expect(shown, `${sel} at 1440x900`).not.toBe('none');
    expect(shown, `${sel} at 1440x900`).not.toBe('absent');
  }
});
