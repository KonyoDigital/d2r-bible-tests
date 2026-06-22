// v381 — COMPLETE base-item database (508 bases scraped from diablo2.io, RotW-current) drives
// _baseTier + _socketMaxFor + base ID cards, and 507 base sprites are registered. Includes the new
// Reign-of-the-Warlock Warlock offhand books (Grimoire/Tome/Codex tiers).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v381 complete base database', () => {
  test.beforeEach(async ({ page }) => { await page.goto(URL); await page.waitForTimeout(2000); });

  test('BASE_DB has the full ~500 bases with tier + maxSockets', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      const db = w.BASE_DB || {};
      const keys = Object.keys(db);
      return {
        count: keys.length,
        withTier: keys.filter(k => db[k].tier).length,
        withSockets: keys.filter(k => db[k].maxSockets != null).length,
        cryptic: w._baseRec('Cryptic Sword'),
      };
    });
    expect(r.count).toBeGreaterThan(490);
    expect(r.withTier).toBeGreaterThan(490);
    expect(r.withSockets).toBeGreaterThan(400);
    expect(r.cryptic.tier).toBe('elite');
    expect(r.cryptic.maxSockets).toBe(4);
  });

  test('the new RotW Warlock book bases are in the DB', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      return { occultCodex: w._baseRec('Occult Codex'), tome: w._baseRec('Tome') };
    });
    expect(r.occultCodex).toBeTruthy();
    expect(r.occultCodex.rotw).toBe(1);
    expect(r.tome).toBeTruthy();
  });

  test('BASE_DB feeds _socketMaxFor + _baseTier for any base', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      return {
        greatPoleaxeMax: w._socketMaxFor('Great Poleaxe'),  // elite polearm, 6
        warPikeTier: w._baseTier('War Pike'),                // elite
        ringMailMax: w._socketMaxFor('Ring Mail'),           // 3
      };
    });
    expect(r.greatPoleaxeMax).toBe(6);
    expect(r.warPikeTier).toBe('elite');
    expect(r.ringMailMax).toBe(3);
  });
});
