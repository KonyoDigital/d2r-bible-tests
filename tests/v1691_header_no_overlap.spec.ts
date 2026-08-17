// v1691 — GEOMETRY, NOT CLASS NAMES. v1690's render gate PASSED a header collision that was
// visibly live on the board: the identity chip (bd-sigil / bs-name / bs-code / bs-glyph) sat on
// top of the masthead title. The render gate's own collision probe used a CLASS-BASED selector —
// `[class*=pill]`, `[class*=identity]` — and the offending element carries neither word in its
// class or its id, so the probe returned 0 collisions while the screenshot beside it showed the
// chip lying across the title. The picture was right; the instrument was hunting for a word that
// does not exist in this DOM. (Grok, looking at the same screenshots, refused it twice.)
//
// This gate cannot make that mistake: the DETECTION never names a class, an id or a component.
// It sweeps every VISIBLE text-bearing element inside `.header`, takes bounding rects, and fails
// on any pairwise intersection above a hairline tolerance. `.header` is the ONE class name in this
// file's detection path, and it is a region boundary — "which part of the page am I policing" —
// never a guess at which component might be the offender. That distinction is the whole bug: the
// old probe had to know the culprit's name in advance, and it guessed wrong.
//
// Three things this file does that a naive geometry sweep does not, each one a measured hole:
//
//  1. NON-VACUITY ON THE VERY ELEMENT IN QUESTION. A leaf-count floor alone cannot tell "the chip
//     does not overlap" apart from "the chip never painted". The chip is genuinely conditional —
//     `<button id="bd-sigil" … hidden>` is unhidden only by JS, `body.app-ctx` hides it outright,
//     and `@media (max-width:900px)` kills it one pixel below our narrowest width. So the sweep
//     must SEE the chip's three labels before any green counts. We assert on their TEXT — what the
//     user reads — never on their class or id, so the detection stays class-blind.
//
//  2. A PINNED INPUT. The chip's label is derived from `d2r_installId`, which a fresh browser
//     context generates at random, and the label's WIDTH is what decides whether it reaches the
//     title. Measured on the broken tree: the longest draw ("Crimson Reliquary") collides at
//     1440px, the shortest ("Dusk Oath") does not. Unpinned, this gate's verdict at a marginal
//     width was a coin flip. Both extremes now run at every width.
//
//  3. NO CONTAINMENT FALSE POSITIVES. A parent and a child that both carry their own text always
//     "intersect" by containment. Measured today: 0 such pairs in this header — but one markup
//     edit (`<div>text <span>text</span></div>`) would make this gate permanently, unfixably red,
//     so ancestor/descendant pairs are excluded by `Node.contains`, not by hope.
//
// WIDTHS. 901 / 1280 / 1920 are the reported band; 1100 sits deliberately BETWEEN the two known-bad
// widths, and 1440 / 1600 cover the band the layout fix's own `@media (min-width:1501px)` leaves
// unmeasured. A fix verified only at the widths that failed is a fix fitted to its own test.
//
// WHAT THIS GATE DOES NOT COVER — stated so nobody reads its green as more than it is. It detects
// elements LYING ON each other. It does not detect the second half of v1691's report: nav labels
// scrolled or cut off inside the tab strip at wide widths. That is a scroller-overflow condition,
// and in this header a horizontally scrollable strip legitimately overflows at narrow widths, so
// "content wider than its box" cannot be asserted here without naming the component this gate
// refuses to name. That class needs its own gate; this one would report it green.
//
// SEEN RED, BOTH DIRECTIONS (never trust a gate nobody has watched fail). Against the header with
// the chip on its absolute rail: 901 → 3 collisions (title × chip name 1332px², × code 303px², ×
// glyph 213px²), 1100 → 3 (name 2184px²), 1280 → 2 (name 2021px²), 1440 → 1 (glyph 323px², long
// draw only). With the chip taken off that rail: 0 collisions at all six widths and both draws,
// leaf count and all three chip labels unchanged — so the green is a fix, not a disappearance.
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

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const WIDTHS = [901, 1100, 1280, 1440, 1600, 1920];
const TOLERANCE_PX = 1; // hairline/anti-aliasing slop only — not a real-overlap allowance
const MIN_LEAVES = 20;  // measured: 24 text-bearing elements at every width and both draws

// The chip's label is a pure function of `d2r_installId` (window.D2R_SIGIL.of), so pinning the id
// pins the three strings the chip renders. These two ids were chosen by exhausting that function
// for its widest and narrowest name — the two ends of the ~2× label-width spread that decides
// whether the chip reaches the title at a marginal width. Set in the Playwright context only:
// an isolated file:// origin created per test, never the browser profile Konyo plays with.
const SIGILS = [
  { draw: 'longest',  installId: 'v1691fixture245', name: 'Crimson Reliquary', code: '346B', glyph: 'ᚹ' },
  { draw: 'shortest', installId: 'v1691fixture13',  name: 'Dusk Oath',         code: 'D3B1', glyph: 'ᛖ' },
];

type Rect = { x: number; y: number; width: number; height: number };
type Leaf = { i: number; tag: string; text: string; rect: Rect; contains: number[] };
type Sweep = { error?: string; leaves?: Leaf[] };

function intersection(a: Rect, b: Rect, tol: number): number {
  const w = Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x);
  const h = Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y);
  if (w <= tol || h <= tol) return 0;
  return w * h;
}

function where(r: Rect): string {
  return `(${r.x.toFixed(1)},${r.y.toFixed(1)} ${r.width.toFixed(1)}x${r.height.toFixed(1)})`;
}

// Collects every element inside `.header` that is visible and carries its own (non-inherited)
// text, plus, for each one, the indices of the other collected elements it CONTAINS. Nothing in
// here reads a class, an id, a tag whitelist or a component name — only computed style, text
// nodes, bounding rects and DOM ancestry.
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
    var els = [];
    Array.prototype.forEach.call(header.querySelectorAll('*'), function (el) {
      if (isVisible(el) && ownText(el)) els.push(el);
    });
    var leaves = els.map(function (el, i) {
      var r = el.getBoundingClientRect();
      var contains = [];
      els.forEach(function (other, j) { if (i !== j && el.contains(other)) contains.push(j); });
      return {
        i: i,
        tag: el.tagName.toLowerCase(),
        text: ownText(el).slice(0, 32),
        rect: { x: r.x, y: r.y, width: r.width, height: r.height },
        contains: contains
      };
    });
    return { leaves: leaves };
  })()
`;

test.describe('v1691 header no-overlap (pure geometry)', () => {
  for (const sigil of SIGILS) {
    for (const width of WIDTHS) {
      test(`T-${width}/${sigil.draw}: no two visible header text elements intersect`, async ({ page }) => {
        await page.setViewportSize({ width, height: 1000 });
        await page.addInitScript(`localStorage.setItem('d2r_installId', ${JSON.stringify(sigil.installId)})`);
        await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(1200); // the chip is painted by script, then unhidden

        const result = (await page.evaluate(SWEEP_SCRIPT)) as Sweep;
        expect(result.error, result.error).toBeUndefined();
        const leaves = result.leaves as Leaf[];
        const texts = leaves.map((l) => l.text);

        // NON-VACUITY. A sweep that measured nothing, or that measured everything EXCEPT the chip
        // this gate exists for, must not be allowed to read as green.
        expect(
          leaves.length,
          `only ${leaves.length} text-bearing header elements found (expected >= ${MIN_LEAVES}); ` +
            `the sweep, not the layout, is the suspect: [${texts.join(' | ')}]`
        ).toBeGreaterThanOrEqual(MIN_LEAVES);

        for (const label of [sigil.name, sigil.code, sigil.glyph]) {
          expect(
            texts,
            `the identity chip's "${label}" was never measured at ${width}px — a green here would ` +
              `mean the chip did not render, not that it stopped covering the title. Measured: ` +
              `[${texts.join(' | ')}]`
          ).toContain(label);
        }

        // DETECTION. Pairwise rect intersection; ancestor/descendant pairs skipped because their
        // overlap is containment, not collision.
        const collisions: string[] = [];
        for (let i = 0; i < leaves.length; i++) {
          for (let j = i + 1; j < leaves.length; j++) {
            const a = leaves[i];
            const b = leaves[j];
            if (a.contains.includes(j) || b.contains.includes(i)) continue;
            const area = intersection(a.rect, b.rect, TOLERANCE_PX);
            if (area > 0) {
              collisions.push(
                `"${a.tag}:${a.text}" @ ${where(a.rect)} overlaps "${b.tag}:${b.text}" @ ` +
                  `${where(b.rect)} — intersection area ${area.toFixed(1)}px²`
              );
            }
          }
        }
        expect(
          collisions,
          `${collisions.length} header collision(s) at ${width}px (${sigil.draw} sigil draw):\n` +
            collisions.join('\n')
        ).toEqual([]);
      });
    }
  }
});
