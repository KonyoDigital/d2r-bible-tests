import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v301 — expanded EXTRA_ITEMS to ~34 top-tier "best of the best" profiles (rare jewelry,
// rare jewels, crafted jackpots, godly runeword bases, charms) that rival runewords/uniques,
// each with a value tier. Discoverable via the 💰 High-Value Finds browser (#hvf-card) and
// routable to per-rarity reference cards (incl. the new 'basic' grey runeword-base cards).

test.describe('v301 high-value finds', () => {
  test.beforeEach(async ({ page }) => { await page.goto(BIBLE); await page.waitForTimeout(500); });

  test('EXTRA_ITEMS holds the expanded top-tier set across categories', async ({ page }) => {
    const r = await page.evaluate(() => {
      const E = (window as any).EXTRA_ITEMS || {};
      const cats: Record<string, number> = {};
      Object.values(E).forEach((e: any) => { cats[e.cat || 'Other'] = (cats[e.cat || 'Other'] || 0) + 1; });
      return { count: Object.keys(E).length, cats };
    });
    expect(r.count).toBeGreaterThanOrEqual(30);
    expect(r.cats['Runeword bases']).toBeGreaterThan(5);
    expect(r.cats['Rare jewelry']).toBeGreaterThan(3);
    expect(r.cats['Crafted']).toBeGreaterThan(2);
  });

  test('the High-Value Finds browser renders all items, grouped + filterable', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab('tools'));
    await page.evaluate(() => {
      const c = document.getElementById('hvf-card');
      if (c && c.classList.contains('collapsed')) (window as any).toggleCardCollapse('hvf-card');
      (window as any).renderHighValueFinds();
    });
    await page.waitForTimeout(150);
    const rows = await page.locator('#hvf-list .hvf-row').count();
    expect(rows).toBeGreaterThanOrEqual(30);
    expect(await page.locator('#hvf-list .hcr-cat').count()).toBeGreaterThan(3); // category headers
    // filter narrows it
    await page.fill('#hvf-filter', 'eth');
    await page.waitForTimeout(120);
    const filtered = await page.locator('#hvf-list .hvf-row').count();
    expect(filtered).toBeGreaterThan(0);
    expect(filtered).toBeLessThan(rows);
  });

  test('a godly runeword BASE routes to a grey base-item reference card', async ({ page }) => {
    await page.evaluate(() => (window as any).openDrop('Eth Berserker Axe (Grief/BotD base)'));
    await page.waitForTimeout(220);
    const card = page.locator('#item-detail .extra-item-card');
    await expect(card).toBeVisible();
    await expect(card).toContainText('Grief');
    await expect(card).toContainText('value = base type'); // the 'basic' roll-line
  });

  test('a crafted jackpot routes to an orange crafted reference card with value tier', async ({ page }) => {
    await page.evaluate(() => (window as any).openDrop('Crafted Caster Amulet (jackpot)'));
    await page.waitForTimeout(220);
    const card = page.locator('#item-detail .extra-item-card');
    await expect(card).toBeVisible();
    const color = await card.locator('.gic-name').evaluate(el => getComputedStyle(el).color);
    expect(color).toBe('rgb(255, 168, 0)'); // #ffa800 crafted orange
  });
});
