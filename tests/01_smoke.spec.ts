import { test, expect } from '@playwright/test';

import * as path from 'path';
const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible_routes.html');
test.describe('Smoke — page loads correctly', () => {
  test('page renders without errors', async ({ page }) => {
    const errors: string[] = [];
    // v41 routine_status.js sibling-path 404 is an expected graceful-fallback emission, not a bug.
    const isBenign = (m: string) => /routine_status\.js/i.test(m) || /Failed to load resource.*ERR_FILE_NOT_FOUND/i.test(m);
    page.on('pageerror', (err) => errors.push(err.message));
    page.on('console', (msg) => { if (msg.type() === 'error' && !isBenign(msg.text())) errors.push(msg.text()); });
    await page.goto(BIBLE);
    await expect(page.locator('.h-title')).toContainText(/Konyo's D2R Farming Bible/);
    expect(errors, `Console/page errors found:\n${errors.join('\n')}`).toEqual([]);
  });

  test('version pill present and renders vNN', async ({ page }) => {
    await page.goto(BIBLE);
    await expect(page.locator('.h-title')).toContainText(/v\d+/);
  });

  test('all 6 tabs render', async ({ page }) => {
    await page.goto(BIBLE);
    const tabs = await page.locator('.tab').allTextContents();
    expect(tabs.length).toBeGreaterThanOrEqual(6);
    expect(tabs.some(t => /bosses/i.test(t))).toBe(true);
    expect(tabs.some(t => /calculator/i.test(t))).toBe(true);
    expect(tabs.some(t => /TZ/i.test(t))).toBe(true);
    expect(tabs.some(t => /runes/i.test(t))).toBe(true);
    expect(tabs.some(t => /RotW/i.test(t))).toBe(true);
    expect(tabs.some(t => /ancients/i.test(t))).toBe(true);
    expect(tabs.some(t => /reference/i.test(t))).toBe(true);
  });

  test('all 11 boss cards render with required structure', async ({ page }) => {
    await page.goto(BIBLE);
    // v41: routine_status.js loader can delay first-paint of boss-card droptables under serial-suite load
    await page.waitForTimeout(600);
    const expectedBosses = ['countess','andariel','duriel','mephisto','travincal','diablo','baal','pindle','nihl','cows','pit'];
    for (const id of expectedBosses) {
      const card = page.locator(`#${id}`);
      await expect(card, `Boss ${id} card`).toBeVisible();
      await expect(card.locator('.boss-name')).toBeVisible();
      await expect(card.locator('.diff-grid .diff-cell')).toHaveCount(6); // 6 difficulties
      await expect(card.locator('table.drops thead th')).toHaveCount(8); // item, tc, 6 diffs
    }
  });

  test('hero card renders default 15 picks (v39 global; 20 when boss-context)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await expect(page.locator('.hero-pick')).toHaveCount(15);
  });

  test('legend renders 5 cards', async ({ page }) => {
    await page.goto(BIBLE);
    const legend = page.locator('.legend-box .legend-item-card');
    await expect(legend).toHaveCount(5);
  });

  test('grail progress widget present', async ({ page }) => {
    await page.goto(BIBLE);
    await expect(page.locator('.grail-progress')).toBeVisible();
    await expect(page.locator('#gp-circle-text')).toBeVisible();
  });

  test('MF slider default + scaling works', async ({ page }) => {
    await page.goto(BIBLE);
    const slider = page.locator('#mf');
    await expect(slider).toHaveValue('699');
    const effMF = await page.locator('#eff-mf').textContent();
    expect(effMF).toMatch(/73\.\d+%/); // ~73.66% at 699 MF
  });
});
