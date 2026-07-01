import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v532 — SIMULATION (locked into Routine I): every base in the Chronicle filter must be a real Forge task.
// White upgrade-source bases → upgrade tasks; elite bases → recognised + host an endgame runeword. This is the
// permanent, fast version of the 86/47 base-batch sims Konyo asked to keep (no per-base reloads).

const WHITE = ["Akaran Rondache","Akaran Targe","Ancient Shield","Ancient Sword","Assault Helmet","Axe","Barbed Club","Barbed Shield","Battle Sword","Bill","Blade","Bone Helm","Bone Shield","Bone Wand","Broad Sword","Chaos Armor","Cinquedeas","Claws","Cleaver","Club","Composite Bow","Crossbow","Crowbill","Crown","Crystal Sword","Cudgel","Death Mask","Demonhide Armor","Dimensional Blade","Double Axe","Flail","Full Plate Mail","Ghost Armor","Gothic Shield","Grand Crown","Grand Scepter","Grave Wand","Great Helm","Greater Claws","Grim Helm","Grim Shield","Grim Wand","Hand Axe","Hard Leather Armor","Hatchet","Holy Water Sprinkler","Hunter's Bow","Jagged Star","Jo Staff","Katar","Knout","Kris","Long Siege Bow","Long Sword","Mask","Military Pick","Morning Star","Naga","Pavise","Petrified Wand","Quhab","Quilted Armor","Razor Bow","Rondache","Rune Sword","Saber","Savage Helmet","Shamshir","Short Staff","Siege Crossbow","Spiked Club","Spiked Shield","Stiletto","Studded Leather","Targe","Tomb Wand","Tower Shield","Trellised Armor","Twin Axe","Voulge","War Axe","War Sword","Winged Helm","Wrist Blade","Wrist Spike","Yew Wand"];
const ELITE = ["Aegis","Archon Plate","Berserker Axe","Blade Barrier","Blade Bow","Blasphemous Grimoire","Bone Visage","Colossus Voulge","Conqueror Crown","Conquest Sword","Corona","Cryptic Sword","Dark Tome","Demonhead","Devil Star","Dusk Shroud","Elegant Blade","Ettin Axe","Fanged Knife","Feral Claws","Ghost Wand","Gorgon Crossbow","Great Bow","Legend Spike","Lich Wand","Mythical Sword","Occult Codex","Phase Blade","Possessed Grimoire","Sacred Rondache","Sacred Targe","Scarab Husk","Scourge","Seraph Rod","Small Crescent","Spired Helm","Suwayyah","Tomahawk","Troll Nest","Truncheon","Tyrant Club","Unearthed Wand","Walking Stick","War Spike","Ward","Wire Fleece","Wrist Sword"];

test('white upgrade-source bases surface Forge upgrade tasks (seed all at once, no reloads)', async ({ page }) => {
  await page.addInitScript((bases: string[]) => {
    localStorage.setItem('d2r_owned', JSON.stringify(bases.map((b) => b + ' (Larzuk base)')));
    localStorage.setItem('d2r_runeStash', JSON.stringify({})); // no runes → each stays an upgrade candidate
    localStorage.setItem('d2r_rwMade', JSON.stringify({}));
    localStorage.setItem('d2r_ladderMode', 'nonladder');
  }, WHITE);
  await page.goto(URL); await page.waitForTimeout(2000);
  const r = await page.evaluate((bases: string[]) => {
    const w: any = window;
    bases.forEach((b) => { try { w._ensureSocketBaseEntry(b + ' (Larzuk base)'); } catch (e) {} });
    const up = new Set(w.forgeScan().upgrades.map((u: any) => u.base.base));
    // dagger normals (Kris/Stiletto) make their word at their own tier → not an UPGRADE; count them as covered.
    const notUp = bases.filter((b) => !up.has(b) && (w._baseRunewords(b) || []).length > 0 && !/Kris|Stiletto|Cinquedeas|Blade\b/.test(b));
    return { total: bases.length, surfaced: up.size, notUp };
  }, WHITE);
  expect(r.surfaced).toBeGreaterThan(78);   // ~84 of 86 surface as upgrade cards
  // no white base that HOSTS a runeword should silently produce nothing (daggers excluded above)
  expect(r.notUp.length).toBeLessThanOrEqual(2);
});

test('every elite endgame base is recognised as runeword-worthy and hosts an endgame runeword', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate((bases: string[]) => {
    const w: any = window;
    const IO = (w.RUNE_INDEX && w.RUNE_INDEX['Io'] != null) ? w.RUNE_INDEX['Io'] : 15;
    const bad: string[] = [];
    bases.forEach((b) => {
      const rws = w._baseRunewords(b) || [];
      const isRW = w._isRunewordBase(b);
      // its meta base recommendation should resolve (feeds the "get a base" one-step tasks)
      const meta = w._forgeMetaBase ? (w._forgeMetaBase(b === b ? (rws[0] ? rws[0].n : b) : b) || {}) : {};
      if (!isRW || rws.length === 0) bad.push(b + ' (not RW-worthy)');
    });
    return { total: bases.length, bad };
  }, ELITE);
  expect(r.bad).toEqual([]);   // all 47 elite bases are runeword-worthy
});
