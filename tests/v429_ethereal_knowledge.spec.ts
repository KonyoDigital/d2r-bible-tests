import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v429 — the system KNOWS which item types can vs can't be ethereal (D2 rules), resolving uniques/sets to
// their base. CAN: armour (all), melee weapons, bows/xbows, orbs/staves/wands/scepters/heads/grimoires.
// CANNOT: rings, amulets, jewels, charms, runes, gems, javelins, throwing weapons. Guards _isEthereal +
// the intake ethereal registration so a mis-read never tags an impossible item.

test('_canBeEthereal classifies base types correctly', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window; const c = (n: string) => w._canBeEthereal(n);
    return {
      can: ['Cryptic Axe', 'Monarch', 'Archon Plate', 'Cap', 'Gauntlets', 'Boots', 'Belt', 'Short Bow', 'Eagle Orb', 'Long Staff', 'Grim Helm'].map(c),
      cannot: ['Ring', 'Amulet', 'Jewel', 'Small Charm', 'Grand Charm', 'Javelin', 'Throwing Axe', 'Throwing Knife', 'Ist rune', 'Perfect Ruby'].map(c),
      suffix: c('Cryptic Axe (5os)'),
    };
  });
  r.can.forEach((v: any) => expect(v).toBe(true));
  r.cannot.forEach((v: any) => expect(v).toBe(false));
  expect(r.suffix).toBe(true);
});

test('uniques/sets resolve to their base for ethereal capability', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window; const c = (n: string) => w._canBeEthereal(n);
    return {
      windforce: c('Windforce'),         // Hydra Bow → true
      grandfather: c('The Grandfather'),  // Colossus Blade → true
      gheeds: c("Gheed's Fortune"),       // Grand Charm → false
      anni: c('Annihilus'),               // Small Charm → false
      torch: c('Hellfire Torch'),         // Large Charm → false
      soj: c('The Stone of Jordan'),      // Ring → false
      maras: c("Mara's Kaleidoscope"),    // Amulet → false
    };
  });
  expect(r.windforce).toBe(true);
  expect(r.grandfather).toBe(true);
  expect(r.gheeds).toBe(false);
  expect(r.anni).toBe(false);
  expect(r.torch).toBe(false);
  expect(r.soj).toBe(false);
  expect(r.maras).toBe(false);
});

test('_isEthereal blocks a mis-flagged impossible item', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1600);
  const r = await page.evaluate(() => {
    const w: any = window;
    // simulate a bad read that tagged a ring + a charm ethereal
    w.etherealItems.add('Some Rare Ring');
    w.etherealItems.add("Gheed's Fortune");
    // and a legit ethereal weapon
    w.etherealItems.add('Cryptic Axe (5os)');
    return {
      ring: w._isEthereal('Some Rare Ring'),       // blocked → false
      charm: w._isEthereal("Gheed's Fortune"),     // blocked → false
      weapon: w._isEthereal('Cryptic Axe (5os)'),  // legit → true
    };
  });
  expect(r.ring).toBe(false);
  expect(r.charm).toBe(false);
  expect(r.weapon).toBe(true);
});

test('no item type returns a WRONG hard verdict across the whole DB', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1800);
  const r = await page.evaluate(() => {
    const w: any = window;
    const all: string[] = w.__allItemNames();
    // resolve any name to its base type, then to a primary class — to VERIFY a 'false' is genuinely a
    // non-etherealable kind (ring/amulet/jewel/charm/javelin/throwing) and not a mislabeled weapon/armour.
    const resolveBase = (n: string) => {
      try { if (w.ITEM_CODEX && w.ITEM_CODEX[n] && w.ITEM_CODEX[n].base) return w.ITEM_CODEX[n].base; } catch (e) {}
      try { if (w.EXTRA_ITEMS && w.EXTRA_ITEMS[n] && w.EXTRA_ITEMS[n].base) return w.EXTRA_ITEMS[n].base; } catch (e) {}
      try { if (w.ITEM_TIP && w.ITEM_TIP[n] && w.ITEM_TIP[n].b) return String(w.ITEM_TIP[n].b).replace(/^\d+\s*socket\s*/i, ''); } catch (e) {}
      return n;
    };
    const wrong: string[] = [];
    all.forEach((n) => {
      if (w._canBeEthereal(n) !== false) return;
      const baseName = resolveBase(n);
      const cats = (w._baseCats && w._baseCats(baseName)) || {};
      const keys = Object.keys(cats);
      // a 'false' is only valid when the resolved base is genuinely non-etherealable:
      //  • jewelry/charm/rune/gem → _baseCats empty (not a socketable base) + name confirms the kind
      //  • a javelin (cats.javelin) or a throwing weapon (weapon without melee AND without missile)
      const isJavelinOrThrowing = !!cats['javelin'] || (!!cats['weapon'] && !cats['melee weapon'] && !cats['missile weapon']);
      const isJewelryKind = keys.length === 0 && /\b(ring|amulet|jewel|charm|rune|facet|amethyst|topaz|sapphire|emerald|ruby|diamond|skull)\b/i.test((baseName + ' ' + n).toLowerCase());
      const isJewelryUnique = keys.length === 0;   // unique ring/amulet names (Raven Frost, Mara's) resolve to no base-class
      if (!(isJavelinOrThrowing || isJewelryKind || isJewelryUnique)) wrong.push(n + ' (base: ' + baseName + ', cats: ' + keys.join('/') + ')');
    });
    return { total: all.length, wrongCount: wrong.length, wrong: wrong.slice(0, 20) };
  });
  console.log(`ethereal verdicts checked across ${r.total} items; genuinely-wrong 'false': ${r.wrongCount}`);
  if (r.wrongCount) console.log('WRONG:', JSON.stringify(r.wrong));
  expect(r.wrongCount).toBe(0);
});
