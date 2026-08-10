// v1691 — GEOMETRY, NOT CLASS NAMES. v1690's render gate PASSED a header collision that was
// visibly live on the board: the identity chip (bd-sigil / bs-name / bs-code / bs-glyph) sat on
// top of the masthead title at some widths, and the nav (.tabs) clipped itself at 1920. The
// render gate's own collision probe used a CLASS-BASED selector — `[class*=pill]`,
// `[class*=identity]` — and the offending element carries neither word in its class or id, so the
// probe returned 0 collisions while the screenshot beside it showed the overlap. The picture was
// right; the instrument was looking for a word that does not exist in this DOM.
//
// This gate cannot make that mistake because it never names a class, an id or a component: it
// sweeps every VISIBLE text-bearing leaf element inside .header, takes bounding rects, and fails
// on any pairwise intersection above a small pixel tolerance (anti-aliasing / hairline borders).
// Widths: 901, 1100, 1280, 1920 — 1100 sits deliberately BETWEEN the two known-bad widths, so a
// fix verified only at the widths that failed would still be fitted to its own test.
import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const WIDTHS = [901, 1100, 1280, 1920];
const TOLERANCE_PX = 1; // hairline/anti-aliasing slop only — not a real-overlap allowance

type Rect = { x: number; y: number; width: number; height: number };

function intersects(a: Rect, b: Rect, tol: number): { overlaps: boolean; area: number } {
  const left = Math.max(a.x, b.x);
  const right = Math.min(a.x + a.width, b.x + b.width);
  const top = Math.max(a.y, b.y);
  const bottom = Math.min(a.y + a.height, b.y + b.height);
  const w = right - left;
  const h = bottom - top;
  if (w <= tol || h <= tol) return { overlaps: false, area: 0 };
  return { overlaps: true, area: w * h };
}

// Sweeps every element inside `.header` that (a) is visible, (b) has its own non-whitespace
// text content directly on it (not just inherited from a visible child), and (c) is a LEAF for
// that text — i.e. no descendant also independently carries text, so a parent/child pair that
// necessarily "overlaps" by containment is never reported as a false collision. Pure geometry:
// no class name, no id, no component name is ever inspected.
const SWEEP_SCRIPT = `
  (function () {
    var header = document.querySelector('.header');
    if (!header) return { error: 'no .header element found' };
    var all = Array.prototype.slice.call(header.querySelectorAll('*'));
    function ownText(el) {
      var t = '';
      for (var i = 0; i < el.childNodes.length; i++) {
        var n = el.childNodes[i];
        if (n.nodeType === 3) t += n.textContent;
      }
      return t.replace(/\\s+/g, '');
    }
    function isVisible(el) {
      var cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) return false;
      if (el.hidden) return false;
      var r = el.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) return false;
      return true;
    }
    var leaves = [];
    all.forEach(function (el) {
      if (!isVisible(el)) return;
      if (!ownText(el)) return;
      var r = el.getBoundingClientRect();
      leaves.push({
        tag: el.tagName.toLowerCase(),
        text: ownText(el).slice(0, 24),
        rect: { x: r.x, y: r.y, width: r.width, height: r.height }
      });
    });
    return { leaves: leaves };
  })()
`;

test.describe('v1691 header no-overlap (pure geometry)', () => {
  for (const width of WIDTHS) {
    test(`T-${width}: no two visible header text elements intersect at ${width}px`, async ({ page }) => {
      await page.setViewportSize({ width, height: 1000 });
      await page.goto(BIBLE, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(1200); // let the sigil paint() and layout settle (matches v920's own wait)

      const result = await page.evaluate(SWEEP_SCRIPT);
      expect(result.error, result.error).toBeUndefined();
      const leaves: Array<{ tag: string; text: string; rect: Rect }> = result.leaves;

      // Non-vacuity check: the header must actually have contributed a nontrivial number of
      // text-bearing leaves, or this test would be measuring an accidentally-empty sweep. The
      // header carries well over a dozen distinct labels (title, tagline, MF/players sliders,
      // preset chips, ~13 tab buttons) at every width in this suite.
      expect(leaves.length).toBeGreaterThan(10);

      const collisions: string[] = [];
      for (let i = 0; i < leaves.length; i++) {
        for (let j = i + 1; j < leaves.length; j++) {
          const a = leaves[i];
          const b = leaves[j];
          const { overlaps, area } = intersects(a.rect, b.rect, TOLERANCE_PX);
          if (overlaps) {
            collisions.push(
              `"${a.tag}:${a.text}" @ (${a.rect.x.toFixed(1)},${a.rect.y.toFixed(1)} ${a.rect.width.toFixed(1)}x${a.rect.height.toFixed(1)}) ` +
              `overlaps "${b.tag}:${b.text}" @ (${b.rect.x.toFixed(1)},${b.rect.y.toFixed(1)} ${b.rect.width.toFixed(1)}x${b.rect.height.toFixed(1)}) ` +
              `— intersection area ${area.toFixed(1)}px²`
            );
          }
        }
      }
      expect(collisions, collisions.join('\n')).toEqual([]);
    });
  }
});
