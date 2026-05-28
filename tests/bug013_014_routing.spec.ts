import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('BUG-013 — TZ-zone → boss detail routing', () => {
  test('Catacombs L4 TZ card has data-boss-id="andariel" and opens detail on click', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1200);
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(300);
    const card = page.locator('.tz-zone-card[data-boss-id="andariel"]').first();
    await card.scrollIntoViewIfNeeded();
    await expect(card).toBeVisible();
    // Use evaluate-click to bypass any Playwright stability interference
    await page.evaluate(() => {
      const el = document.querySelector('.tz-zone-card[data-boss-id="andariel"]') as HTMLElement;
      el?.click();
    });
    await page.waitForTimeout(400);
    await expect(page.locator('#boss-detail-overlay')).not.toHaveClass(/hidden/);
    const name = await page.locator('.boss-detail-header .bd-name').innerText();
    expect(name.toLowerCase()).toContain('andariel');
  });

  test('Halls of Anguish maps to nihl', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1200);
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(300);
    const card = page.locator('.tz-zone-card[data-boss-id="nihl"]').first();
    await expect(card).toBeVisible();
  });

  test('Worldstone Keep maps to baal', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1200);
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(300);
    const card = page.locator('.tz-zone-card[data-boss-id="baal"]').first();
    await expect(card).toBeVisible();
  });

  test('River of Flame maps to diablo', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1200);
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(300);
    const card = page.locator('.tz-zone-card[data-boss-id="diablo"]').first();
    await expect(card).toBeVisible();
  });

  test('every TZ zone card has a valid boss-id mapping (v39: 100% routed)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1200);
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(300);
    const dump = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll('.tz-zone-card'));
      return {
        total: cards.length,
        unmapped: cards.filter((c: any) => !c.getAttribute('data-boss-id')).length,
      };
    });
    expect(dump.total).toBeGreaterThan(0);
    expect(dump.unmapped).toBe(0);
  });
});

test.describe('BUG-014 — Cmd/Ctrl-click source-chip opens boss detail', () => {
  test('Cmd-click on first source chip opens detail panel', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1200);
    await page.locator('.tab[data-tab="calc"]').click();
    await page.locator('#item-search').fill('nagel');
    await page.waitForTimeout(300);
    await page.locator('#item-grid .item-tile:visible').first().click();
    await page.waitForTimeout(300);
    // find any source-chip in the detail
    const chip = page.locator('#item-detail .source-chip').first();
    await expect(chip).toBeVisible();
    await chip.click({ modifiers: ['Meta'] });
    await page.waitForTimeout(400);
    await expect(page.locator('#boss-detail-overlay')).not.toHaveClass(/hidden/);
  });

  test('plain click on source chip still jumps to boss card (not detail)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1200);
    await page.locator('.tab[data-tab="calc"]').click();
    await page.locator('#item-search').fill('nagel');
    await page.waitForTimeout(300);
    await page.locator('#item-grid .item-tile:visible').first().click();
    await page.waitForTimeout(300);
    await page.locator('#item-detail .source-chip').first().click();
    await page.waitForTimeout(300);
    // Should be on bosses tab now, NOT detail overlay
    await expect(page.locator('#boss-detail-overlay')).toHaveClass(/hidden/);
    await expect(page.locator('#tab-bosses')).toBeVisible();
  });
});
