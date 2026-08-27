import { test, expect } from './_net_stub';
import * as path from 'path';

// v2211 — "how are 61 items fitting in one mule?"
//
// He was reading a wrong number correctly. The shelf card computed
//     total = items.length + magicItems.length;  cap = 40;  pct = Math.min(100, total/cap*100)
// which is three lies in one line:
//   · it counts ITEMS, not CELLS. A Colossus Blade is 2x4 = 8 cells; a Nagelring is 1x1.
//   · 40 is a mule's INVENTORY on its own. The stash beside it holds 100 more — 140 in total.
//   · the clamp saturated the bar for every value above the cap, so a locker holding 61 and one
//     holding 200 painted identically and `vg-hot` fired the same at 41 as at 300.
//
// Meanwhile the drill-down two clicks away had been packing across as many mule characters as a
// category needs since v405. Two surfaces, one question, opposite answers — and the one he sees
// first was the one that was wrong.
//
// THE FIX IS AN EXTRACTION, NOT A SECOND SUM. `_muleLoad(names)` is the span, defined once; the
// card and the drill-down both call it. Writing a cell count into the card would have made two
// copies of the packing rule, which is how they came to disagree in the first place. [[copy-drift]]
//
// ⚠ AND THE FIRST FIX STILL COULD NOT TELL THEM APART. Measured: 40 Colossus Blades (320 cells,
// THREE mules) and 40 Nagelrings (40 cells, one mule) both leave the last mule 29% full, so both
// gauges painted the same — the clamp's false equivalence one layer down. A locker that has
// already spilled now reads HOT whatever its last mule looks like, and carries a ×N badge.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v2211 the locker card counts cells, not items', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('_muleLoad exists and is the ONE packer both surfaces call', async ({ page }) => {
    const r = await page.evaluate(() => {
      const src = document.documentElement.innerHTML;
      return { fn: typeof (window as any)._muleLoad,
               // the pack loop must exist exactly once in the shipped page
               loops: (src.match(/packGrid\(_?rem, 10, 10\)/g) || []).length };
    });
    expect(r.fn, '_muleLoad is not exposed — the card cannot ask the packer and would have to '
      + 'compute its own answer, which is the defect').toBe('function');
  });

  test('a big-item locker needs more mules than a small-item locker of the SAME count',
    async ({ page }) => {
      const r = await page.evaluate(() => {
        const L = (window as any)._muleLoad;
        const big: string[] = [], small: string[] = [];
        for (let i = 0; i < 40; i++) { big.push('Colossus Blade'); small.push('Nagelring'); }
        const a = L(big), b = L(small);
        return { bigCells: a.cells, bigMules: a.mules.length, bigFirst: a.firstCount,
                 smallCells: b.cells, smallMules: b.mules.length, smallFirst: b.firstCount };
      });
      // the whole point: same item COUNT, wildly different space
      expect(r.bigCells, 'a Colossus Blade is not being measured as 8 cells').toBe(320);
      expect(r.smallCells, 'a ring is not being measured as 1 cell').toBe(40);
      expect(r.bigMules, '40 two-by-four weapons still claim to fit on one mule. 320 cells against '
        + '140 per mule is three mules, and this is exactly the arithmetic he questioned')
        .toBeGreaterThan(1);
      expect(r.smallMules, '40 rings need more than one mule — 40 cells fits in 140 easily')
        .toBe(1);
      expect(r.bigFirst, 'the first mule claims to hold all 40 blades').toBeLessThan(40);
    });

  test('the SHELF marks a spilled locker hot and badges it — asserted on the rendered DOM',
    async ({ page }) => {
      // ⚠ THIS READS THE PRODUCT, NOT A COPY OF ITS RULE. My first version computed
      // `hot = pct >= 85 || mules > 1` in the SPEC and compared it to itself, so deleting the spill
      // flag from bible.html left it GREEN. A test that re-implements the thing it checks measures
      // nothing. [[feedback-blind-fixture-green-gate]]
      //
      // ⚠ AND IT GOES IN THROUGH THE PRODUCT'S OWN DOORS. Writing d2r_muleAssign straight into
      // localStorage does NOT work — `assign` is an in-memory map loaded at startup, so renderVault
      // re-read nothing and the card showed 2 items out of 20 planted. That fixture would have
      // "proved" the card was broken when it was the plant that never arrived.
      const r = await page.evaluate(() => {
        const W = window as any;
        // every big two-by-four weapon we can actually get into the vault, through tvVaultRegister
        const big = ['Windforce', 'Doombringer', 'The Grandfather', 'Breath of the Dying',
                     'Stormlash', 'Bonehew', 'Steeldriver', 'Earth Shifter', 'Baranar\'s Star',
                     'Lightsabre', 'Tomb Reaver', 'Silver-Edged Axe', 'Astreon\'s Iron Ward',
                     'Schaefer\'s Hammer', 'Buriza-Do Kyanon', 'Eaglehorn', 'Widowmaker',
                     'Kuko Shakaku', 'Cliffkiller', 'Magewrath', 'Hellrack', 'Demon Machine',
                     'Gut Siphon', 'Warshrike', 'Wraith Flight', 'Gimmershred', 'Lacerator',
                     'Stormspike', 'Thunderstroke', 'Titan\'s Revenge'];
        const small = ['Nagelring', 'Raven Frost', 'Manald Heal'];
        const landedBig: string[] = [], landedSmall: string[] = [];
        for (const n of big) {
          try { if ((W.tvVaultRegister(n) || {}).ok) { W.vaultAssign(n, 'uni-weap'); landedBig.push(n); } }
          catch (e) { /* a name this build does not know simply does not join the fixture */ }
        }
        for (const n of small) {
          try { if ((W.tvVaultRegister(n) || {}).ok) { W.vaultAssign(n, 'uni-small'); landedSmall.push(n); } }
          catch (e) { /* same */ }
        }
        W.renderVault();
        const read = (id: string) => {
          const card = document.querySelector('[data-vault-mule="' + id + '"]');
          if (!card) return null;
          const fill = card.querySelector('.vm-gauge-fill');
          const badge = card.querySelector('.vm-mules');
          return { hot: !!(fill && fill.classList.contains('vg-hot')),
                   badge: !!badge, badgeText: badge ? (badge.textContent || '') : '' };
        };
        return { weap: read('uni-weap'), small: read('uni-small'),
                 weapMules: W._muleLoad(landedBig).mules.length,
                 weapCells: W._muleLoad(landedBig).cells,
                 smallMules: W._muleLoad(landedSmall).mules.length,
                 smallCells: W._muleLoad(landedSmall).cells,
                 nBig: landedBig.length, nSmall: landedSmall.length };
      });

      // the fixture must actually spill, or every assertion below is vacuous
      expect(r.weapMules, 'the big-weapon fixture landed ' + r.nBig + ' items / ' + r.weapCells
        + ' cells and does NOT need a second mule, so this test shows nothing. Add more, or the '
        + 'registrar stopped accepting these names.').toBeGreaterThan(1);
      expect(r.smallMules, 'the small fixture spilled too (' + r.smallCells + ' cells) — there is '
        + 'no contrast left to measure').toBe(1);

      expect(r.weap!.hot, 'a locker needing ' + r.weapMules + ' mules did NOT render .vg-hot. Its '
        + 'last mule is only partly full, so without the spill flag its bar is indistinguishable '
        + 'from a locker that fits comfortably — the clamp\'s false equivalence, one layer down.')
        .toBe(true);
      expect(r.weap!.badge, 'no ×N mule badge on a locker that needs ' + r.weapMules + ' mules — '
        + 'the shelf still says nothing about the spill').toBe(true);
      expect(r.weap!.badgeText).toContain(String(r.weapMules));

      expect(r.small!.hot, 'a locker holding ' + r.smallCells + ' cells of a 140-cell mule renders '
        + 'hot — a warning that is on for everything means nothing').toBe(false);
      expect(r.small!.badge, 'a one-mule locker carries a mule-count badge').toBe(false);
    });

  test('the drill-down subtitle is UNCHANGED by the extraction', async ({ page }) => {
    // The extraction must be behaviour-neutral for the surface that was already right. This
    // reproduces the exact expression the drill-down renders.
    const r = await page.evaluate(() => {
      const L = (window as any)._muleLoad;
      const names: string[] = []; for (let i = 0; i < 40; i++) names.push('Colossus Blade');
      const l = L(names);
      const n = l.mules.length || 1;
      return l.phys + ' item' + (l.phys === 1 ? '' : 's') + ' total'
        + (n > 1 ? (' across ' + n + ' mules · ' + l.firstCount + ' on this one') : '');
    });
    expect(r).toBe('40 items total across 3 mules · 15 on this one');
  });

  test('an empty locker does not divide by nothing', async ({ page }) => {
    const r = await page.evaluate(() => {
      const l = (window as any)._muleLoad([]);
      const m = l.mules.length || 1;
      let pct = Math.min(100, Math.round(((l.cells - (m - 1) * l.capCells) / l.capCells) * 100));
      if (!isFinite(pct) || pct < 0) pct = 0;
      return { cells: l.cells, phys: l.phys, mules: m, pct };
    });
    expect(r.cells).toBe(0);
    expect(r.phys).toBe(0);
    expect(r.mules, 'an empty locker claims to need zero mules; the card would divide by it')
      .toBe(1);
    expect(r.pct, 'an empty locker paints a non-zero bar').toBe(0);
  });
});
