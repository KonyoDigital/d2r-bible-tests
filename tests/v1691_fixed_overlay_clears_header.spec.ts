// v1691.1 — THE OTHER HALF OF "NOTHING IN THE HEADER COVERS ANYTHING ELSE".
//
// v1691's sibling gate (v1691_header_no_overlap.spec.ts) sweeps text-bearing elements INSIDE
// `.header` and it is honest in its own header comment that `.header` is its region boundary — so
// anything fixed-positioned OVER the header is out of its scope by construction. That blind spot
// had a live occupant the same day: `#v687-build-badge`, `position:fixed; top:6px; left:8px`, a
// child of <body> and not of `.header`, drawn straight through the start of the masthead title.
// The board read "o's D2R Farming Bible" with "Kony" buried under the build stamp. Grok, given
// only the screenshot, said the K was hidden; the sibling gate said 0 collisions. Both were right
// about their own question. This file asks the question neither of them was asking.
//
// DETECTION, and it names no component. Every element in the document whose COMPUTED position is
// `fixed` and which is not a descendant of `.header` is an overlay candidate; every visible
// element inside `.header` carrying its own text is a target; any pairwise intersection above a
// hairline fails. Nothing here greps for "badge", a class or an id — the next offender will be a
// different element with a different name, exactly as the chip was last time.
//
// THE FIXTURE LIED ONCE ALREADY, SO IT IS PINNED TWICE OVER:
//  1. THE CLAIM BAR. A fresh browser context has an UNCLAIMED install, so `#claim-bar` renders
//     120px tall above `.header` and pushes the masthead row clear of a badge fixed at y=6. My
//     first probe of this very bug reported GREEN at all ten widths for exactly that reason while
//     the screenshots showed the collision. Konyo's install is claimed. The bar is removed before
//     every measurement, and its removal is asserted, so a green can never come from 120px of
//     fixture padding.
//  2. THE NARROW WIDTHS ARE THE POINT. The title is CENTRED, so its left edge marches rightwards
//     as the viewport widens and the collision lives at the BOTTOM of the range, not the top:
//     measured on the broken tree, title/art left edge 204.5px @721, 294.5 @901, 361.7 @1100 vs a
//     badge ending at 378.6px — red at 721/760/820/901/1000, clear by 1280. A gate that only ran
//     at 1280+ (where the reported failures were seen) would have called this fixed forever.
//     720px is the badge's own `display:none` cutoff, so 721 is the true worst case.
//
// SEEN RED (a gate nobody has watched fail proves nothing): run against a copy of the pre-fix
// bible.html via BIBLE_PATH, this file fails at 721/760/820/901/1000 with intersections of
// 2945.9 / 2555.9 / 1955.9 / 1145.9 / 414.7 px² of build badge over H1.h-title, and passes at
// 1100+. After the fix (badge capped to 180px border-box with an ellipsis) the clearance is
// 16.5px at 721 and grows monotonically; the badge still paints, still says v-id and date first.
//
// WHAT THIS DOES NOT COVER: an overlay that is `absolute` inside a non-header stacking context, an
// icon or background image lying over text (nothing here reads paint, only boxes), and truncated
// nav labels. Those are separate gates.
// v1754 — through the shared net stub, so this spec's measurements do not depend on the
// runner reaching fonts.googleapis.com. bible.html makes exactly FIVE external requests and
// all five are fonts; stubbing them removes the whole external surface.
//
// ⚠ NOT because a failed font collapses this layout — I checked, and it does not. Measured
// three ways, .set-card-header is 78px ONLINE, 78px OFFLINE and 78px STUBBED. The v1749
// note on _net_stub says a font failure makes that bar 0px; offline does not reproduce it,
// and the flake it was written about turned out to be a blind toggleCardCollapse leaving
// the card COLLAPSED (fixed in v1751, proven by forcing .collapsed). The honest reason to
// stub here is determinism, not a defect anyone has shown. [[inherited_claim_is_not_evidence]]
import { test, expect } from './_net_stub';
import * as path from 'path';

const BIBLE = 'file://' + (process.env.BIBLE_PATH || path.resolve(__dirname, '..', 'bible.html'));
// 721 is the badge's own display:none boundary + 1 — the worst case, not the prettiest one.
const WIDTHS = [721, 820, 901, 1000, 1100, 1280, 1920];
const TOLERANCE_PX = 1; // hairline/anti-aliasing slop only — not a real-overlap allowance
const MIN_LEAVES = 15;  // measured: 21 text-bearing header elements at 721-820, 24 at 901+

type Rect = { x: number; y: number; width: number; height: number };
type Hit = { overlay: string; target: string; text: string; area: number; a: Rect; b: Rect };
type Sweep = { error?: string; claimBar?: boolean; leaves?: number; overlays?: number; hits?: Hit[] };

const SWEEP_SCRIPT = `
  (function () {
    var header = document.querySelector('.header');
    if (!header) return { error: 'no .header element found' };
    function ownText(el) {
      var t = '';
      for (var i = 0; i < el.childNodes.length; i++) {
        var n = el.childNodes[i];
        if (n.nodeType === 3) t += n.textContent;
      }
      return t.replace(/\\s+/g, ' ').trim();
    }
    function isVisible(el) {
      var cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
      if (el.hidden) return false;
      var r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    }
    function name(el) {
      return el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
        (el.className && typeof el.className === 'string' && el.className.trim()
          ? '.' + el.className.trim().split(/\\s+/)[0] : '');
    }
    var targets = [];
    Array.prototype.forEach.call(header.querySelectorAll('*'), function (el) {
      if (isVisible(el) && ownText(el)) targets.push(el);
    });
    var overlays = [];
    Array.prototype.forEach.call(document.body.querySelectorAll('*'), function (el) {
      if (header.contains(el) || el.contains(header)) return;
      if (getComputedStyle(el).position !== 'fixed') return;
      if (!isVisible(el)) return;
      overlays.push(el);
    });
    var hits = [];
    overlays.forEach(function (o) {
      var a = o.getBoundingClientRect();
      targets.forEach(function (t) {
        var b = t.getBoundingClientRect();
        var w = Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x);
        var h = Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y);
        if (w <= ${TOLERANCE_PX} || h <= ${TOLERANCE_PX}) return;
        hits.push({
          overlay: name(o), target: name(t), text: ownText(t).slice(0, 32), area: w * h,
          a: { x: a.x, y: a.y, width: a.width, height: a.height },
          b: { x: b.x, y: b.y, width: b.width, height: b.height },
        });
      });
    });
    return {
      claimBar: !!document.getElementById('claim-bar'),
      leaves: targets.length, overlays: overlays.length, hits: hits,
    };
  })()
`;

function where(r: Rect): string {
  return `(${r.x.toFixed(1)},${r.y.toFixed(1)} ${r.width.toFixed(1)}x${r.height.toFixed(1)})`;
}

for (const width of WIDTHS) {
  test(`no fixed overlay lies on header text @${width}px (claimed install)`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(BIBLE);
    await page.waitForTimeout(900); // fonts + the JS that appends the badge and paints the chip

    // Konyo's install is CLAIMED: no 120px #claim-bar, so the masthead row sits at the very top of
    // the viewport — which is where a fixed top-left overlay lives. Leaving the bar in place is
    // what made the first probe of this bug report a false green.
    await page.evaluate(() => {
      const bar = document.getElementById('claim-bar');
      if (bar) bar.remove();
      document.body.classList.remove('has-claim-bar');
    });
    await page.waitForTimeout(150);

    const sweep = (await page.evaluate(SWEEP_SCRIPT)) as Sweep;
    expect(sweep.error, `sweep failed @${width}`).toBeUndefined();
    expect(sweep.claimBar, `#claim-bar still present @${width} — the fixture would hide the bug`).toBe(false);

    // NON-VACUITY. Green must mean "measured and clear", never "there was nothing to measure".
    expect(sweep.leaves!, `only ${sweep.leaves} text-bearing header elements @${width}`)
      .toBeGreaterThanOrEqual(MIN_LEAVES);
    expect(sweep.overlays!, `no fixed overlay found at all @${width} — this gate measured nothing`)
      .toBeGreaterThanOrEqual(1);
    // and specifically: the build stamp must have PAINTED, and must still answer "is this stale?"
    const badge = page.locator('#v687-build-badge');
    await expect(badge).toBeVisible();

    // THE GEOMETRY IS ASSERTED FIRST, ON PURPOSE. The two cosmetic guards below (stamp format,
    // width cap) also go red on the broken tree, and if they ran first they would abort the test
    // before the overlap check ever executed — a gate whose real assertion nobody has watched fail.
    const report = sweep.hits!
      .sort((x, y) => y.area - x.area)
      .map(h => `  ${h.overlay} ${where(h.a)} lies on ${h.target} "${h.text}" ${where(h.b)} — ${h.area.toFixed(1)}px²`)
      .join('\n');
    expect(sweep.hits!.length,
      `@${width}px — ${sweep.hits!.length} fixed overlay(s) covering header text:\n${report}`).toBe(0);

    // The stamp must still answer "is this tab stale?" — id and date, before any decoration, and
    // the box that carries them must stay bounded. An unbounded stamp is what caused the collision.
    const stamp = ((await badge.textContent()) || '').trim();
    expect(stamp, `build badge text @${width}`).toMatch(/^v\d+\s+·\s+\d{4}-\d{2}-\d{2}/);
    const box = await badge.boundingBox();
    expect(box!.width, `build badge is ${box!.width}px wide @${width} — an unbounded stamp is the bug`)
      .toBeLessThanOrEqual(200);
  });
}
