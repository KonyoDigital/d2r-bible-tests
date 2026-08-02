import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v1591 — AN EMPTY CODE LIST MEANS "NO CONSTRAINT", NOT "NOTHING".
//
// Konyo: "Loot Filter needs to be fixed also.. its not correctly filtering out the garbage items i
// dont need."
//
// Every base rule in the generated filter is populated from the live "still to farm" set, and v553
// wrote the assumption into a comment: "Empty = show no bases, consistent with the count". It is
// the opposite. The mod treats a rule with an empty equipmentItemCode as UNCONSTRAINED — on import
// it drops the empty key entirely, leaving `Show Base Items` as rarity:[normal] + quality:[all],
// which matches EVERY white item in the game.
//
// So the filter INVERTED ITSELF the moment his Chronicle sealed 99/99: with no runewords left to
// forge there are no wanted bases, every base list came out empty, and four rules silently became
// catch-alls. The better his chronicle got, the worse the filter behaved.
//
// The inversion cuts both ways and the hides are the dangerous half: `Hide Magic Wanted Bases` with
// an empty list stops meaning "hide magic copies of the bases I want" and starts meaning "hide
// EVERY magic, rare and low-quality item" — rare circlets included.
//
// This spec pins the invariant that fixes it: a rule whose live code list is empty must be
// DISABLED, because "target nothing" cannot be expressed as an empty list — only as a rule that
// does not run.

async function board(page: any) {
  await page.goto(URL);
  await page.waitForTimeout(2400);
}

async function filterJson(page: any, which = 'endgame') {
  return page.evaluate(async (w: string) => {
    let captured: string | null = null;
    try { (navigator as any).clipboard.writeText = async (t: string) => { captured = t; }; } catch (e) {}
    await (window as any).copyLootFilter(w);
    return captured ? JSON.parse(captured) : null;
  }, which);
}

const META = new Set(['name', 'enabled', 'ruleType', 'filterEtherealSocketed']);

test.describe('v1591 — no enabled rule may be left unconstrained', () => {
  test('★ every ENABLED rule that targets item codes actually has some', async ({ page }) => {
    await board(page);
    const f = await filterJson(page);
    expect(f, 'the endgame filter must generate').toBeTruthy();
    const bad = (f.rules || [])
      .filter((r: any) => r.enabled && Array.isArray(r.equipmentItemCode) && r.equipmentItemCode.length === 0)
      .map((r: any) => `${r.ruleType} · ${r.name}`);
    expect(bad,
      'an enabled rule with an EMPTY equipmentItemCode is a catch-all: a show floods the screen ' +
      'with every white item, a hide swallows every magic/rare drop. Disable it instead.\n' +
      'offenders: ' + JSON.stringify(bad)).toEqual([]);
  });

  test('★ a sealed chronicle must not turn the filter into a firehose', async ({ page }) => {
    // The exact regression: no wanted bases left ⇒ the base rules must go QUIET, not wide open.
    await board(page);
    const r = await page.evaluate(async () => {
      const w: any = window;
      const eb = w._endgameFilterBases({});
      let captured: string | null = null;
      try { (navigator as any).clipboard.writeText = async (t: string) => { captured = t; }; } catch (e) {}
      await w.copyLootFilter('endgame');
      const f = JSON.parse(captured as any);
      const byName = (n: string) => (f.rules || []).find((x: any) => x.name === n);
      return {
        wantedBases: (eb.codes || []).length,
        plain: (eb.plainCodes || []).length,
        showBase: (() => { const x = byName('Show Base Items'); return x && { on: !!x.enabled, codes: (x.equipmentItemCode || []).length }; })(),
        showEth: (() => { const x = byName('3. Show ETH and Socket bases'); return x && { on: !!x.enabled, codes: (x.equipmentItemCode || []).length }; })(),
        trashHide: (() => { const x = byName('1. Hide Trash Gear'); return x && { on: !!x.enabled, codes: (x.equipmentItemCode || []).length }; })(),
      };
    });
    if (r.plain === 0) {
      expect(r.showBase.on,
        'no premium plain bases wanted, so the plain-white show must be OFF — enabled with an ' +
        'empty list is what showed every white item in the game').toBe(false);
    }
    if (r.wantedBases === 0) {
      expect(r.showEth.on, 'no wanted bases, so the eth/socket show must be OFF').toBe(false);
    }
    // and the trash hide must still be doing its job, or we have merely traded one failure for another
    expect(r.trashHide.on, 'the trash hide must stay ON').toBe(true);
    expect(r.trashHide.codes, 'and must still carry the base codes it hides').toBeGreaterThan(100);
  });

  test('the value rules are untouched — this fix must not cost him drops', async ({ page }) => {
    await board(page);
    const f = await filterJson(page);
    const on = (n: string) => {
      const r = (f.rules || []).find((x: any) => x.name === n);
      return !!(r && r.enabled);
    };
    for (const n of ['2. Show Uniques and Sets', '4. Show Charms Skillers Sunders', '5. Show Gems',
                     '6. Show Runes Sunder Mats High', '7. Show Shards Essences Uber Mat',
                     '8. Show Potions', '9. Show Jewels Rings Amulets', 'Show Rare Rings and Amulets']) {
      expect(on(n), `${n} must still be enabled — hiding garbage must not hide loot`).toBe(true);
    }
  });

  test('the cousin filter obeys the same invariant', async ({ page }) => {
    // Same generator, different opts. A fix applied to one profile and not the other is the class
    // sweep this project keeps paying for.
    await board(page);
    const f = await filterJson(page, 'cousin');
    if (!f) test.skip(true, 'no cousin profile in this build');
    const bad = (f.rules || [])
      .filter((r: any) => r.enabled && Array.isArray(r.equipmentItemCode) && r.equipmentItemCode.length === 0)
      .map((r: any) => `${r.ruleType} · ${r.name}`);
    expect(bad, 'cousin profile has unconstrained enabled rules: ' + JSON.stringify(bad)).toEqual([]);
  });
});
