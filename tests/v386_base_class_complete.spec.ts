import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v386 — EVERY base in BASE_DB resolves to its accurate D2 item class via the game-data BASE_CLASS map
// (weapons.txt/armor.txt `type` column), consulted first by _baseCats. Fixes the regex gaps that left
// flails (Flail/Scourge), daggers (Poignard/Mithril Point), orbs, druid pelts, necro shrunken heads,
// barb helms, claws & Templar Coat with NO category at all — which mislabeled a Scourge as a generic Mace.
test.describe('v386 base-class completeness (game-data driven)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1500);
  });

  test('every BASE_DB base resolves to at least one category — zero gaps', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      const empties: string[] = [];
      for (const n of Object.keys(w.BASE_DB || {})) {
        if (!Object.keys(w._baseCats(n)).length) empties.push(n);
      }
      return { total: Object.keys(w.BASE_DB || {}).length, empties };
    });
    expect(r.total).toBeGreaterThan(500);
    expect(r.empties, `bases with no category: ${r.empties.join(', ')}`).toEqual([]);
  });

  test('the flail line is mace-class (Scourge is a flail, NOT a generic mace mislabel) + gets mace runewords', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      const cats = (n: string) => Object.keys(w._baseCats(n));
      const rwNames = (n: string) => w._baseRunewords(n).map((x: any) => x.n);
      return {
        scourge: cats('Scourge'),
        flail: cats('Flail'),
        knout: cats('Knout'),
        scourgeRW: rwNames('Scourge'),
      };
    });
    expect(r.scourge).toContain('mace');
    expect(r.flail).toContain('mace');
    expect(r.knout).toContain('mace');
    // a mace-class base gets real mace runewords (e.g. Black, a 3os Maces/Hammers/Clubs word)
    expect(r.scourgeRW).toContain('Black');
  });

  test('newly-categorized classes: daggers, druid pelts, necro shrunken heads, orbs', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      const cats = (n: string) => Object.keys(w._baseCats(n));
      return {
        poignard: cats('Poignard'),         // dagger
        mithrilPoint: cats('Mithril Point'),// dagger (was a straggler)
        wolfHead: cats('Wolf Head'),        // druid pelt → helm
        preservedHead: cats('Preserved Head'), // necro shrunken head → voodoo head
        eagleOrb: cats('Eagle Orb'),        // sorc orb
        templarCoat: cats('Templar Coat'),  // body armor
        headRW: w._baseRunewords('Preserved Head').map((x: any) => x.n),
        orbRW: w._baseRunewords('Eagle Orb').length,
      };
    });
    expect(r.poignard).toContain('dagger');
    expect(r.mithrilPoint).toContain('dagger');
    expect(r.wolfHead).toContain('helm');
    expect(r.preservedHead).toContain('voodoo head');
    expect(r.eagleOrb).toContain('orb');
    expect(r.templarCoat).toContain('body armor');
    expect(r.headRW).toContain('Vigilance');  // the one shrunken-head runeword now matches
    expect(r.orbRW).toBe(0);                  // orbs have NO runewords — no false matches
  });
});
