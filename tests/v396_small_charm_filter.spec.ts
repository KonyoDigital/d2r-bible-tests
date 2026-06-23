import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v396 — the magic small-charm KEEP/JUNK filter + valuable-charm reference cards. _smallCharmKeep keeps only
// the rolls D2 traders pay for (5%+ MF, any all-res, 10%+ single res, 10+ life, 5% FHR — combos = OP) and
// throws out junk (stamina/gold/+1 stat/low single res/low MF). The valuable types are EXTRA_ITEMS reference
// cards (own ID card + #arttip hover + search + UNI-SMALL routing) with the HD small-charm sprite.
test.describe('v396 small-charm filter + reference cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1500);
  });

  test('_smallCharmKeep keeps valuable rolls, flags combos OP, throws out junk', async ({ page }) => {
    const r = await page.evaluate(() => {
      const k = (window as any)._smallCharmKeep;
      return {
        mf7: k(['7% Better Chance of Getting Magic Items']),
        allres: k(['All Resistances +5']),
        life20: k(['+20 to Life']),
        fhr: k(['+5% Faster Hit Recovery']),
        combo: k(['All Resistances +5', '7% Better Chance of Getting Magic Items']),
        junkStam: k(['+12 Maximum Stamina']),
        junkLowMf: k(['3% Better Chance of Getting Magic Items']),
        junkAr: k(['+24 to Attack Rating']),
        junkLowRes: k(['Fire Resist +5%']),
      };
    });
    expect(r.mf7.keep).toBe(true);
    expect(r.allres.keep).toBe(true);
    expect(r.life20.keep).toBe(true);
    expect(r.fhr.keep).toBe(true);
    expect(r.combo.keep).toBe(true);
    expect(r.combo.op).toBe(true);          // 2+ good affixes = OP perfect
    expect(r.junkStam.keep).toBe(false);
    expect(r.junkLowMf.keep).toBe(false);   // 3% MF is below the 5% bar
    expect(r.junkAr.keep).toBe(false);
    expect(r.junkLowRes.keep).toBe(false);  // single 5% res is not a keeper (10%+ is)
  });

  test('each valuable small charm has an EXTRA_ITEMS reference card with HD art + real affixes', async ({ page }) => {
    const r = await page.evaluate(() => {
      const names = [
        'Small Charm of Good Luck (7% MF)',
        'Shimmering Small Charm (5% All Res)',
        'Small Charm of Vita (20 Life)',
        'Shimmering Small Charm of Good Luck (5 res + 7 MF)',
      ];
      const w = window as any;
      const out: Record<string, any> = {};
      for (const n of names) {
        out[n] = {
          inExtra: !!w.findExtraItem(n),
          art: w.artUrl(n),
          cardLen: (w.extraItemDetailHtml(n) || '').length,
        };
      }
      return out;
    });
    for (const n of Object.keys(r)) {
      expect(r[n].inExtra, `${n} resolvable`).toBeTruthy();
      expect(r[n].art, `${n} HD art`).toBe('art/hd_charm_small.png');
      expect(r[n].cardLen, `${n} renders a card`).toBeGreaterThan(500);
    }
  });

  test('no console errors with the charm reference cards loaded', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    page.on('pageerror', (e) => errs.push(e.message));
    await page.evaluate(() => { (window as any).openDrop && (window as any).openDrop('Shimmering Small Charm of Vita (5 res + 20 life)'); });
    await page.waitForTimeout(200);
    expect(errs).toEqual([]);
  });
});
