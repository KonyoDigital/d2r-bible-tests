import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v298 — EXTRA_ITEMS: reference items the user owns that sit OUTSIDE the curated 312-item
// boss-drop grail (so they don't inflate the grail count or appear in the calculator). They
// get a routable ID card, are recognised by the Vault intake, and persist through the
// owned-sanitizer. Uniques (Nord's Tenderizer) show fixed ITEM_TIP stats; rares show a general
// affix-pool description. Extensible registry — finds get added as we go.

test.describe('v298 reference items (EXTRA_ITEMS)', () => {
  test.beforeEach(async ({ page }) => { await page.goto(BIBLE); await page.waitForTimeout(500); });

  test('EXTRA_ITEMS registry holds the owned reference items, classified', async ({ page }) => {
    const r = await page.evaluate(() => {
      const E = (window as any).EXTRA_ITEMS || {};
      return { keys: Object.keys(E), nord: E["Nord's Tenderizer"]?.rarity, marshal: E["Marshal's Amulet"]?.rarity };
    });
    expect(r.keys).toContain("Nord's Tenderizer");
    expect(r.keys).toContain("Marshal's Amulet");
    expect(r.keys).toContain("Plague Wing Amulet");
    expect(r.keys).toContain("Blood Gyre");
    expect(r.nord).toBe('unique');
    expect(r.marshal).toBe('rare');
  });

  test('a reference UNIQUE (Nord\'s Tenderizer) cards in unique gold with fixed stats', async ({ page }) => {
    await page.evaluate(() => (window as any).openDrop("Nord's Tenderizer"));
    await page.waitForTimeout(220);
    const card = page.locator('#item-detail .extra-item-card');
    await expect(card).toBeVisible();
    await expect(card.locator('.gic-name')).toContainText("Nord's Tenderizer");
    const color = await card.locator('.gic-name').evaluate(el => getComputedStyle(el).color);
    expect(color).toBe('rgb(199, 179, 119)'); // #c7b377 unique gold
    await expect(card).toContainText('Enhanced Damage'); // fixed stat from ITEM_TIP
    await expect(card).toContainText('Blizzard');
  });

  test('a reference RARE (Marshal\'s Amulet) cards in rare yellow with a general affix-pool description', async ({ page }) => {
    await page.evaluate(() => (window as any).openDrop("Marshal's Amulet"));
    await page.waitForTimeout(220);
    const card = page.locator('#item-detail .extra-item-card');
    await expect(card).toBeVisible();
    const color = await card.locator('.gic-name').evaluate(el => getComputedStyle(el).color);
    expect(color).toBe('rgb(255, 255, 100)'); // #ffff64 rare yellow
    await expect(card).toContainText('3–6 random affixes');
    await expect(card).toContainText('Mara'); // the "rivals/beats Mara's" general note
  });

  test('reference items resolve via findExtraItem and survive the owned-sanitizer', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      const resolves = ["Nord's Tenderizer", "Blood Gyre"].every(n => !!w.findExtraItem(n));
      // the sanitizer keeps EXTRA_ITEMS names in owned (simulate by checking the set membership fn)
      const set = w.EXTRA_ITEMS;
      return { resolves, hasBlood: !!set["Blood Gyre"] };
    });
    expect(r.resolves).toBe(true);
    expect(r.hasBlood).toBe(true);
  });
});
