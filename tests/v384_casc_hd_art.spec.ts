import { test, expect } from './_net_stub';
import * as path from 'path';
import * as fs from 'fs';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v384 — CASC HD ART OVERRIDE. Every matchable item now resolves to its TRUE in-game sprite,
// extracted from the local D2R install (Data CASC → SpA1 .sprite → RGBA PNG, art/hd_*.png).
// The override is Object.assign'd LAST so the genuine local-drive HD wins over every
// mr_/base_/d2io_ backup. Exceptional/elite bases reuse their normal base's sprite via the
// game's `invfile` field (Berserker Axe = elite War Axe → war_axe sprite), exactly as D2R renders.
test.describe('v384 CASC HD art overrides backups everywhere', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('artUrl returns the hd_ sprite for direct + invfile-mapped bases, runes, gems, essences', async ({ page }) => {
    const r = await page.evaluate(() => {
      const t = (window as any).artUrl;
      const want: Record<string, string> = {
        'Kite Shield': 'art/hd_kite_shield.png',
        'Berserker Axe': 'art/hd_war_axe.png',   // elite → normal War Axe sprite (invfile)
        'Monarch': 'art/hd_kite_shield.png',     // elite Kite Shield
        'Archon Plate': 'art/hd_light_plate.png',// elite Light Plate
        'Ith': 'art/hd_ith_rune.png',
        'Essence of Terror': 'art/hd_burning_essence_of_terror.png',
        'Emerald': 'art/hd_emerald.png',
        // codename uniques (dedicated CASC sprites, in-game-typo filenames) + Diablo Clone organs
        'Pus Spitter': 'art/hd_pus_spiter.png',
        'The Chieftain': 'art/hd_the_chieftan.png',
        'Skewer of Krintiz': 'art/hd_krintizs_skewer.png',
        'Witchwild String': 'art/hd_whichwild_string.png',
        "Mephisto's Brain": 'art/hd_brain.png',
        "Baal's Eye": 'art/hd_eye.png',
        "Diablo's Horn": 'art/hd_horn.png',
      };
      const out: Record<string, { got: string; ok: boolean }> = {};
      for (const [n, exp] of Object.entries(want)) out[n] = { got: t(n), ok: t(n) === exp };
      const hdCount = Object.values((window as any).D2IO_ART).filter(
        (v: any) => typeof v === 'string' && v.startsWith('art/hd_')).length;
      return { out, hdCount };
    });
    for (const [n, v] of Object.entries(r.out)) {
      expect(v.ok, `${n} -> ${v.got}`).toBe(true);
    }
    expect(r.hdCount).toBeGreaterThanOrEqual(600);
  });

  test('every hd_ sprite referenced in D2IO_ART exists on disk', async ({ page }) => {
    const refs: string[] = await page.evaluate(() =>
      Array.from(new Set(Object.values((window as any).D2IO_ART)
        .filter((v: any) => typeof v === 'string' && v.startsWith('art/hd_')) as string[])));
    const missing = refs.filter((rel) => !fs.existsSync(path.resolve(__dirname, '..', rel)));
    expect(missing).toEqual([]);
    expect(refs.length).toBeGreaterThanOrEqual(300);
  });
});
