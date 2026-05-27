import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('BUG-023/024 — static tabs render', () => {
  test('Ancients tab shows colossal-ancients mechanics', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('.tab[data-tab="ancients"]').click();
    await page.waitForTimeout(150);
    const tab = page.locator('#tab-ancients');
    await expect(tab).toBeVisible();
    await expect(tab).toContainText(/Talic/i);
    await expect(tab).toContainText(/Korlic/i);
    await expect(tab).toContainText(/Madawc/i);
    await expect(tab).toContainText(/Colossal/i);
    // Enrage stat blocks
    const stats = await tab.locator('.stat').count();
    expect(stats).toBeGreaterThanOrEqual(4);
  });

  test('Reference tab shows TC + qlvl + MF explainers', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('.tab[data-tab="ref"]').click();
    await page.waitForTimeout(150);
    const tab = page.locator('#tab-ref');
    await expect(tab).toBeVisible();
    await expect(tab).toContainText(/TC check/i);
    await expect(tab).toContainText(/qlvl check/i);
    await expect(tab).toContainText(/verified/i);
  });
});
