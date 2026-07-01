// v464 / v535 — CUBE-UP CANDIDATE hint. CORRECTED: only a RARE item on a Normal/Exceptional base can be
// tier-upgraded in the cube (Normal→Exceptional→Elite) KEEPING its affixes. Verified vs game-file cubemain.txt:
// the quality-preserving upgrade recipes accept unique/rare/set only — NOT magic, NOT crafted, NOT white. In the
// Item Checker (magic/rare/crafted keepers) that leaves RARE, and the recipe is the RARE line (P.Sapphire weapon
// / P.Amethyst armor) — NOT the unique line (P.Emerald/P.Diamond). Elite bases + non-gear get no note.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v464 cube-up candidate', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForFunction(() => (window as any)._cubeUpNote && (window as any)._baseTier);
  });

  test('normal-tier RARE weapon → upgrade-to-Exceptional, RARE recipe (P.Sapphire), keeps affixes', async ({ page }) => {
    const note = await page.evaluate(() => {
      eval('magicFinds')['Raven Bite'] = { q: 'rare', base: 'Crystal Sword' };  // Crystal Sword = Normal sword
      return (window as any)._cubeUpNote('Raven Bite');
    });
    expect(note).toContain('Cube-up candidate');
    expect(note).toContain('Exceptional');
    expect(note).toContain('Ort + Amn + Perfect Sapphire');   // RARE weapon recipe (not the unique's Emerald)
    expect(note).toMatch(/KEEPS all affixes/i);
  });

  test('normal-tier RARE armor → upgrade-to-Exceptional, RARE armor recipe (P.Amethyst)', async ({ page }) => {
    const note = await page.evaluate(() => {
      eval('magicFinds')['Soldier Plate'] = { q: 'rare', base: 'Breast Plate' };  // Normal body armor
      return (window as any)._cubeUpNote('Soldier Plate');
    });
    expect(note).toContain('Ral + Thul + Perfect Amethyst');  // RARE armor recipe
  });

  test('exceptional-tier RARE weapon → upgrade-to-Elite, RARE recipe (P.Sapphire)', async ({ page }) => {
    const note = await page.evaluate(() => {
      eval('magicFinds')['Excep Blade'] = { q: 'rare', base: 'Dimensional Blade' };  // Exceptional sword
      return (window as any)._cubeUpNote('Excep Blade');
    });
    expect(note).toContain('Elite');
    expect(note).toContain('Fal + Um + Perfect Sapphire');    // RARE exc→elite weapon recipe
  });

  test('MAGIC item → NO note (magic items cannot be cube-upgraded)', async ({ page }) => {
    const note = await page.evaluate(() => {
      eval('magicFinds')['Soldier Plate'] = { q: 'magic', base: 'Breast Plate' };  // Normal body armor, magic
      return (window as any)._cubeUpNote('Soldier Plate');
    });
    expect(note).toBe('');   // v535 fix: magic can't upgrade → no candidate note
  });

  test('CRAFTED item → NO note (crafted items cannot be cube-upgraded)', async ({ page }) => {
    const note = await page.evaluate(() => {
      eval('magicFinds')['Craft Ammy'] = { q: 'crafted', base: 'Crystal Sword' };
      return (window as any)._cubeUpNote('Craft Ammy');
    });
    expect(note).toBe('');   // v535 fix: crafted can't upgrade → no candidate note
  });

  test('elite base → NO note (already top tier)', async ({ page }) => {
    const note = await page.evaluate(() => {
      eval('magicFinds')['Elite Blade'] = { q: 'rare', base: 'Phase Blade' };  // Elite sword
      return (window as any)._cubeUpNote('Elite Blade');
    });
    expect(note).toBe('');
  });

  test('non-gear (charm) → NO note', async ({ page }) => {
    const note = await page.evaluate(() => {
      eval('magicFinds')['Some Charm'] = { q: 'magic', base: 'Grand Charm' };
      return (window as any)._cubeUpNote('Some Charm');
    });
    expect(note).toBe('');
  });

  test('the hint renders in the magic/rare detail card (rare item)', async ({ page }) => {
    const html = await page.evaluate(() => {
      eval('magicFinds')['Raven Bite'] = { q: 'rare', base: 'Crystal Sword' };
      return (window as any)._magicFindCardHtml('Raven Bite');
    });
    expect(html).toContain('Cube-up candidate');
  });
});
