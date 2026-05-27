import { test, expect } from '@playwright/test';

import * as path from 'path';
const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible_routes.html');
test.describe('Each cell renders the correct state', () => {
  test('blocked-tc cells render with TC-overrun title', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    // Mephisto Norm-TZ caps below SoJ TC60 — TC block, blocked-tc class with TC overrun in title
    const row = page.locator('#mephisto tr[data-item="The Stone of Jordan"]');
    const normTzCell = row.locator('td.diff-col').nth(1);
    await expect(normTzCell).toHaveClass(/blocked-tc/);
    await expect(normTzCell).toHaveAttribute('title', /TC \d+/);
  });

  test('qlvl blocked cells show orange (block-mlvl) class', async ({ page }) => {
    await page.goto(BIBLE);
    // Andariel NM can't drop Mara's (qlvl 67 > NM Andy mlvl 49)
    const row = page.locator('#andariel tr[data-item="Mara\'s Kaleidoscope"]');
    const nmCell = row.locator('td.diff-col').nth(2);
    const cls = await nmCell.getAttribute('class') || '';
    expect(cls).toMatch(/blocked-mlvl/);
  });

  test('best cells in each row are highlighted gold', async ({ page }) => {
    await page.goto(BIBLE);
    // Pick first boss card, verify at least one cell is best-cell
    const bestCells = page.locator('#mephisto td.best-cell');
    const count = await bestCells.count();
    expect(count).toBeGreaterThan(0);
  });

  test('each visible chance cell shows 1:N format or %', async ({ page }) => {
    await page.goto(BIBLE);
    const cells = page.locator('#mephisto td.diff-col:not(.blocked-tc):not(.blocked-mlvl):not(.cannot)');
    const count = await cells.count();
    expect(count).toBeGreaterThan(0);
    for (let i = 0; i < Math.min(count, 10); i++) {
      const text = (await cells.nth(i).textContent())?.trim() || '';
      // should match "1:N" with optional comma or "N%"
      expect(text, `cell ${i}: "${text}"`).toMatch(/^(1:[\d,]+|\d+%|—)$/);
    }
  });

  test('boss tier badges are present', async ({ page }) => {
    await page.goto(BIBLE);
    const tiers = ['S+', 'S', 'A+', 'A', 'A-'];
    for (const tier of tiers) {
      const found = await page.locator(`.boss-tier-val:has-text("${tier}")`).count();
      expect(found, `tier ${tier} should appear`).toBeGreaterThan(0);
    }
  });

  test('every boss row has clickable item name with star + owned button', async ({ page }) => {
    await page.goto(BIBLE);
    const firstRow = page.locator('#mephisto tr.clickable').first();
    await expect(firstRow.locator('.star-btn')).toBeVisible();
    await expect(firstRow.locator('.owned-btn')).toBeVisible();
  });

  test('total item-rows across all bosses ≥ 200', async ({ page }) => {
    await page.goto(BIBLE);
    const rows = page.locator('.boss-card tr.clickable');
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(200);
  });
});
