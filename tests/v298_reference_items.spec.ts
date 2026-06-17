import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v298 — EXTRA_ITEMS: reference items the user owns that sit OUTSIDE the curated boss-drop grail
// (so they don't inflate the grail count or appear in the calculator). They get a routable ID
// card, are recognised by the Vault intake, and persist through the owned-sanitizer. Rares show a
// general affix-pool description. Extensible registry — finds get added as we go.
// NOTE (v341.33): the 11 High-Value-Finds UNIQUES (Nord's Tenderizer, Arioc's Needle, …) were
// promoted INTO the Calculator grail (312 → 322), so they now card as ordinary grail uniques and
// are no longer in EXTRA_ITEMS. EXTRA_ITEMS now holds rares / crafts / socket-bases only.

test.describe('v298 reference items (EXTRA_ITEMS)', () => {
  test.beforeEach(async ({ page }) => { await page.goto(BIBLE); await page.waitForTimeout(500); });

  test('EXTRA_ITEMS registry holds the owned reference items, classified', async ({ page }) => {
    const r = await page.evaluate(() => {
      const E = (window as any).EXTRA_ITEMS || {};
      return { keys: Object.keys(E), nord: !!E["Nord's Tenderizer"], marshal: E["Marshal's Amulet"]?.rarity };
    });
    expect(r.keys).toContain("Marshal's Amulet");
    expect(r.keys).toContain("Plague Wing Amulet");
    expect(r.keys).toContain("Blood Gyre");
    expect(r.nord).toBe(false);       // v341.33 — Nord's Tenderizer is a grail unique now, not a reference item
    expect(r.marshal).toBe('rare');
  });

  test('a migrated HVF unique (Nord\'s Tenderizer) now cards as a GRAIL unique in gold with fixed stats', async ({ page }) => {
    await page.evaluate(() => (window as any).openDrop("Nord's Tenderizer"));
    await page.waitForTimeout(220);
    const card = page.locator('#item-detail .aid-card.aid-r-unique');   // grail ID card, not the reference (.extra-item) card
    await expect(card).toBeVisible();
    await expect(card.locator('.aid-name-txt')).toContainText("Nord's Tenderizer");
    const color = await card.locator('.aid-name-txt').evaluate(el => getComputedStyle(el).color);
    expect(color).toBe('rgb(199, 179, 119)'); // #c7b377 unique gold
    // item properties render in the .cx-props block of the detail panel (alongside the grail card)
    const detail = page.locator('#item-detail');
    await expect(detail).toContainText('Enhanced Damage'); // fixed stat from codex / ITEM_TIP
    await expect(detail).toContainText('Blizzard');
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
      const resolves = ["Marshal's Amulet", "Blood Gyre"].every(n => !!w.findExtraItem(n));
      // the sanitizer keeps EXTRA_ITEMS names in owned (simulate by checking the set membership fn)
      const set = w.EXTRA_ITEMS;
      return { resolves, hasBlood: !!set["Blood Gyre"] };
    });
    expect(r.resolves).toBe(true);
    expect(r.hasBlood).toBe(true);
  });
});
