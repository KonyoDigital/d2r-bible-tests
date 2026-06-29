// v464 — CUBE-UP CANDIDATE hint: a magic/rare/crafted item on a Normal or Exceptional base can be upgraded a
// tier in the cube (Normal→Exceptional→Elite) KEEPING all affixes. Flag it + show the exact recipe. Elite bases
// and non-gear (charms/rings) get no note. Connects the tier info to the upgrade recipes.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v464 cube-up candidate', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForFunction(() => (window as any)._cubeUpNote && (window as any)._baseTier);
  });

  test('normal-tier rare weapon → upgrade-to-Exceptional weapon recipe (keeps affixes)', async ({ page }) => {
    const note = await page.evaluate(() => {
      eval('magicFinds')['Raven Bite'] = { q: 'rare', base: 'Crystal Sword' };  // Crystal Sword = Normal sword
      return (window as any)._cubeUpNote('Raven Bite');
    });
    expect(note).toContain('Cube-up candidate');
    expect(note).toContain('Exceptional');
    expect(note).toContain('Ral + Sol + Perfect Emerald');
    expect(note).toMatch(/KEEPS all affixes/i);
  });

  test('normal-tier magic armor → upgrade-to-Exceptional armor recipe', async ({ page }) => {
    const note = await page.evaluate(() => {
      eval('magicFinds')['Soldier Plate'] = { q: 'magic', base: 'Breast Plate' };  // Normal body armor
      return (window as any)._cubeUpNote('Soldier Plate');
    });
    expect(note).toContain('Tal + Shael + Perfect Diamond');
  });

  test('exceptional-tier base → upgrade-to-Elite recipe', async ({ page }) => {
    const note = await page.evaluate(() => {
      eval('magicFinds')['Excep Blade'] = { q: 'rare', base: 'Dimensional Blade' };  // Exceptional sword
      return (window as any)._cubeUpNote('Excep Blade');
    });
    expect(note).toContain('Elite');
    expect(note).toContain('Lum + Pul + Perfect Emerald');
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

  test('the hint renders in the magic/rare detail card', async ({ page }) => {
    const html = await page.evaluate(() => {
      eval('magicFinds')['Raven Bite'] = { q: 'rare', base: 'Crystal Sword' };
      return (window as any)._magicFindCardHtml('Raven Bite');
    });
    expect(html).toContain('Cube-up candidate');
  });
});
