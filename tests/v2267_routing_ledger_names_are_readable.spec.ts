import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

/* v2267 — THE ITEM NAME WAS THE ONLY THING IN THE ROW ALLOWED TO SHRINK.
 *
 * Measured on the vault tab in the natural state — no fixture, no seeding — ALL 40 .vrg-name cells
 * were clipped at 1440 AND 901 AND 375, with cuts of 73-97%:
 *
 *     Boneslayer Blade     106/3px    97% gone   <- three pixels of the name
 *     Bloodtree Stump      103/9px    91%
 *     Astreon's Iron Ward  122/15px   88%
 *
 * and nothing in the ancestor chain carried a title, so the full name was reachable NOWHERE.
 *
 * ONE ASYMMETRY CAUSED IT. A 233px row held: art 26 (flex 0/0) · NAME (flex 1/1, min-width:0) ·
 * "Low" 32 (flex 0/0) · "→ UNI-WEAPONS" 82 (flex 0/1 but min-width:auto, so it never shrinks below
 * its content) · ✕ 18 · four 8px gaps. The name was the only child that could give, so it absorbed
 * the whole squeeze while the DESTINATION LABEL kept all 82 pixels. The row spent its width saying
 * where the item was going and left three pixels for which item it was.
 *
 * ⚠ AND THE FIRST FIX MOVED THE DEFECT RATHER THAN CURING IT. A min-width floor on the name alone
 * took name-clipping from 40 to 9 and put 40 of 40 TAGS into ellipsis — the column was simply too
 * narrow for its own contents, and every knob inside it was rearranging the same shortfall.
 * Widening the grid floor (250px → 330px, fitting the measured 204px of furniture plus a 122px
 * name) is what actually fixed it.
 *
 * HOW IT WAS FOUND, AND THE NEAR-MISS: a cross-family read of a screenshot reported "vrg-name
 * 119/60". I nearly dismissed it — my first check measured the TOOLS tab, where this table does not
 * render at all, and reported 0 clipped. Suspect the instrument.
 *
 * VENUE: a browser spec. Runs on GitHub CI, never on his Mac. [[test-venue]]
 */
test.describe('v2267 — the routing ledger says WHICH item, not just where it went', () => {
  for (const [w, h, maxCutPct] of [[1440, 1000, 0], [901, 900, 0], [375, 800, 25]] as const) {
    test(`item names are readable at ${w}px`, async ({ page }) => {
      await page.setViewportSize({ width: w, height: h });
      await page.goto(URL);
      await page.waitForTimeout(2200);
      await page.evaluate(() => (window as any).switchTab('vault'));
      await page.waitForTimeout(1200);

      const r = await page.evaluate(() => {
        const names = [...document.querySelectorAll('.vrg-name')] as HTMLElement[];
        const cut = (e: HTMLElement) =>
          e.scrollWidth > 0 ? Math.round((100 * (e.scrollWidth - e.clientWidth)) / e.scrollWidth) : 0;
        const clipped = names.filter((e) => e.scrollWidth > e.clientWidth + 1);
        return {
          rendered: names.length,
          worstCutPct: names.length ? Math.max(...names.map(cut)) : -1,
          worst: clipped
            .map((e) => ({ t: (e.textContent || '').trim(), s: e.scrollWidth, c: e.clientWidth, p: cut(e) }))
            .sort((a, b) => b.p - a.p)
            .slice(0, 4),
          rowsOverflowing: [...document.querySelectorAll('.vrg-row')]
            .filter((r2) => r2.scrollWidth > r2.clientWidth + 1).length,
        };
      });

      /* A SAMPLE OF ZERO PASSES EVERY ASSERTION BELOW. The whole defect lived in this table, so a
         board that renders none of it must refuse rather than report clean. */
      expect(r.rendered, 'no .vrg-name rendered — this test measured NOTHING, which is not a pass')
        .toBeGreaterThan(5);

      expect(r.worstCutPct,
        `an item name is ${r.worstCutPct}% cut with no way to read the rest: ${JSON.stringify(r.worst)}`)
        .toBeLessThanOrEqual(maxCutPct);

      expect(r.rowsOverflowing, 'a routing row is wider than the column holding it').toBe(0);
    });
  }
});
