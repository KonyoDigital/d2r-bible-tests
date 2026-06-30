// v377 — PRECISE base-type → runeword matching. Regression guard for a real-harm bug: a melee weapon
// (scepter) carries the generic "weapon" category, and the old matcher did "missile weapons".indexOf
// ("weapon")>=0 → true, so EVERY melee weapon falsely matched EVERY bow/crossbow (Missile) runeword.
// It told the user a BOW runeword (Edge/Zephyr) fit a Grand Scepter and he socketed real runes on it.
// NO cross-type bleed allowed: missile runewords ONLY on missile weapons, melee ONLY on melee, etc.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v377 runeword base matching', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2000);
  });

  test('a SCEPTER never matches Missile (bow) runewords; does match scepter/melee ones', async ({ page }) => {
    const r = await page.evaluate(() => {
      const names = (a: any[]) => a.map((x) => x.n);
      return names((window as any)._baseRunewords('Grand Scepter'));
    });
    // ⛔ bow/crossbow (Missile Weapons) runewords must NOT appear on a scepter
    expect(r).not.toContain('Edge');     // Edge = 3 socket Missile Weapons
    expect(r).not.toContain('Zephyr');   // Zephyr = 2 socket Missile Weapons
    // ✅ scepter-listed + melee-weapon runewords SHOULD appear
    expect(r).toContain("King's Grace"); // Swords Scepters
    expect(r).toContain('Lawbringer');   // Swords Hammers Scepters
    expect(r).toContain('Malice');       // Melee Weapons
  });

  test('a BOW matches Missile runewords but NOT melee-only ones', async ({ page }) => {
    const r = await page.evaluate(() => {
      const names = (a: any[]) => a.map((x) => x.n);
      return names((window as any)._baseRunewords('Long Bow'));
    });
    expect(r).toContain('Edge');         // Missile Weapons ✓
    expect(r).toContain('Zephyr');       // Missile Weapons ✓
    expect(r).not.toContain('Malice');   // Melee Weapons — a bow is NOT melee
    expect(r).not.toContain('Black');    // Clubs Hammers Maces — not a bow
  });

  test('a SWORD matches sword runewords but not bow/polearm-only ones', async ({ page }) => {
    const r = await page.evaluate(() => {
      const names = (a: any[]) => a.map((x) => x.n);
      return names((window as any)._baseRunewords('Crystal Sword'));
    });
    expect(r).toContain('Spirit');       // Swords or Shields ✓
    expect(r).not.toContain('Edge');     // Missile Weapons — a sword is not missile
  });

  test('CIRCLETS (Circlet/Coronet/Tiara/Diadem) host NO runewords — D2R sockets them for gems/jewels only', async ({ page }) => {
    const r = await page.evaluate(() => {
      const names = (a: any[]) => a.map((x) => x.n);
      const w: any = window;
      return {
        tiara: names(w._baseRunewords('Tiara')),
        circlet: names(w._baseRunewords('Circlet')),
        coronet: names(w._baseRunewords('Coronet')),
        diadem: names(w._baseRunewords('Diadem')),
        // a REAL helm must still host helm runewords (regression guard — circlets are classed 'helm')
        boneVisage: names(w._baseRunewords('Bone Visage')),
      };
    });
    expect(r.tiara).toEqual([]);     // ⛔ no runewords in a Tiara
    expect(r.circlet).toEqual([]);
    expect(r.coronet).toEqual([]);
    expect(r.diadem).toEqual([]);
    expect(r.boneVisage.length).toBeGreaterThan(0);   // ✅ a true helm is unaffected
  });

  test('a helm runeword\'s RECOMMENDED bases (bestStr) never list circlets', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w: any = window;
      // _forgeMetaBase = the engine's recommended-base picker that feeds the "Get a <X> base" prompt
      const names = (w._forgeMetaBase ? w._forgeMetaBase('Delirium').names : []) as string[];
      return names;
    });
    expect(r.length).toBeGreaterThan(0);                 // still recommends real helms
    ['Circlet', 'Coronet', 'Tiara', 'Diadem'].forEach((c) => expect(r).not.toContain(c));
  });

  test('body armor / shield matching is unchanged (no regression)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const names = (a: any[]) => a.map((x) => x.n);
      return {
        archon: names((window as any)._baseRunewords('Archon Plate')),
        monarch: names((window as any)._baseRunewords('Monarch')),
      };
    });
    expect(r.archon).toContain('Enigma');
    expect(r.archon).toContain('Chains of Honor');
    expect(r.archon).not.toContain('Spirit');   // Spirit is swords/shields, not body armor
    expect(r.monarch).toContain('Spirit');       // shield ✓
  });
});
