// v380 — per-item TIER label (Normal/Exceptional/Elite), verified from the game-file base triads.
// Shows "Elite Base Item" / "Elite Unique" / "Elite Set" like diablo2.io, and feeds the engine an extra
// accuracy check. Also: 16 base sprites grabbed from diablo2.io are now registered in D2IO_ART.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v380 item tier label', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2000);
  });

  test('_baseTier resolves the verified Normal/Exceptional/Elite triads', async ({ page }) => {
    const r = await page.evaluate(() => {
      const t = (b: string) => (window as any)._baseTier(b);
      return {
        longSword: t('Long Sword'),       // normal
        runeSword: t('Rune Sword'),        // exceptional
        crypticSword: t('Cryptic Sword'),  // elite
        monarch: t('Monarch'),             // elite shield
        ringMail: t('Ring Mail'),          // normal armor
        archon: t('Archon Plate'),         // elite armor
        unknown: t('Not A Real Base'),     // '' (never guess)
      };
    });
    expect(r.longSword).toBe('normal');
    expect(r.runeSword).toBe('exceptional');
    expect(r.crypticSword).toBe('elite');
    expect(r.monarch).toBe('elite');
    expect(r.ringMail).toBe('normal');
    expect(r.archon).toBe('elite');
    expect(r.unknown).toBe('');
  });

  test('_itemTierLabel: base items, grail uniques (inherit base tier), socketed bases', async ({ page }) => {
    const r = await page.evaluate(() => {
      const L = (n: string) => (window as any)._itemTierLabel(n);
      return {
        longSword: L('Long Sword'),                 // Normal Base Item
        crypticSword: L('Cryptic Sword'),            // Elite Base Item
        frostwind: L('Frostwind'),                   // Elite Unique (cryptic sword)
        grandfather: L('The Grandfather'),           // Elite Unique (colossus blade)
        monarchLarzuk: L('Monarch (Larzuk base)'),   // Elite Base Item
        crystal4os: L('Crystal Sword (4os)'),        // Normal Base Item
      };
    });
    expect(r.longSword).toBe('Normal Base Item');
    expect(r.crypticSword).toBe('Elite Base Item');
    expect(r.frostwind).toBe('Elite Unique');
    expect(r.grandfather).toBe('Elite Unique');
    expect(r.monarchLarzuk).toBe('Elite Base Item');
    expect(r.crystal4os).toBe('Normal Base Item');
  });

  test('the 16 fetched base sprites are registered in D2IO_ART', async ({ page }) => {
    const r = await page.evaluate(() => ({
      dimBlade: (window as any).artUrl('Dimensional Blade'),
      gilded: (window as any).artUrl('Gilded Shield'),
      fuscina: (window as any).artUrl('Fuscina'),
    }));
    expect(r.dimBlade).toContain('base_dimensionalblade');
    expect(r.gilded).toContain('base_gildedshield');
    expect(r.fuscina).toContain('base_fuscina');
  });
});
