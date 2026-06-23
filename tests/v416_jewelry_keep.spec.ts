import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
// v416 — TOP-TIER gate for rolled-name rings · amulets · jewels · large/grand charms.
// Konyo: a junk rare ring (Blood Grip) must be THROWN OUT, not muled; only SoJ/Raven-tier rolls keep.
test('_jewelryKeep gates junk jewelry but keeps top-tier rolls', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1300);
  const r = await page.evaluate(() => {
    const w:any = window; const jk = w._jewelryKeep;
    const k = (mods:string[], base:string) => { const x = jk(mods, base); return x ? (x.keep ? 'keep' : 'throw') : 'null'; };
    return {
      bloodGrip: k(['+34 to Attack Rating','+10 to Energy','+10 to Life','Lightning Resist +5%','Magic Damage Reduced by 2'], 'Ring'),
      dualLeech: k(['6% Life Stolen per Hit','5% Mana Stolen per Hit','+18 to Life','+11 to Dexterity'], 'Ring'),
      casterFCR: k(['10% Faster Cast Rate','+40 to Mana','All Resistances +9'], 'Ring'),
      mediocre2: k(['+22 to Life','Cold Resist +28%'], 'Ring'),
      loaded3:   k(['+24 to Life','Fire Resist +26%','+16 to Strength'], 'Ring'),
      junkAmu:   k(['+15 to Mana','Lightning Resist +6%'], 'Amulet'),
      skiller:   k(['+1 to Fire Skills','+34 to Life'], 'Grand Charm'),
      junkGC:    k(['+12 to Life','+8 to Mana'], 'Grand Charm'),
      facet:     k(['+5% to Fire Skill Damage','-5% to Enemy Fire Resistance'], 'Rainbow Facet'),
      noMods:    k([], 'Ring'),
      notJewelry: k(['+200% Enhanced Damage'], 'Cryptic Axe'),
    };
  });
  expect(r.bloodGrip).toBe('throw');   // the junk ring Konyo flagged
  expect(r.dualLeech).toBe('keep');
  expect(r.casterFCR).toBe('keep');
  expect(r.mediocre2).toBe('throw');   // 2 medium mods isn't SoJ-tier for a ring
  expect(r.loaded3).toBe('keep');
  expect(r.junkAmu).toBe('throw');
  expect(r.skiller).toBe('keep');
  expect(r.junkGC).toBe('throw');
  expect(r.facet).toBe('null');        // facets ungated → always kept
  expect(r.noMods).toBe('null');       // can't judge → kept for manual review
  expect(r.notJewelry).toBe('null');   // weapons/armour rares aren't gated here
});
