import { test, expect } from '@playwright/test';

import * as path from 'path';
const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');
test.describe('Verified anchor data (silospen/pairofdocs)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => { try { (window as any)._buildAllBossDrops && (window as any)._buildAllBossDrops(false); } catch (e) {} }).catch(() => {});
    // Set MF to 300 to match anchor reference (so cells show raw verified numbers)
    await page.locator('#mf').fill('300');
    await page.locator('#mf').dispatchEvent('input');
  });

  test('Mephisto Hell Shako anchor = 1:836 @ 300MF (RoW)', async ({ page }) => {
    const row = page.locator('#mephisto tr[data-item="Harlequin Crest (Shako)"]');
    const hellCell = row.locator('td.diff-col').nth(4); // hell column
    await expect(hellCell).toContainText('1:836');
    await expect(hellCell).toHaveClass(/verified-cell/);
  });

  test('Andariel NM SoJ anchor = 1:2,286 @ 300MF (RoW)', async ({ page }) => {
    const row = page.locator('#andariel tr[data-item="The Stone of Jordan"]');
    const nmCell = row.locator('td.diff-col').nth(2); // nm column
    await expect(nmCell).toContainText('1:2,286');
    await expect(nmCell).toHaveClass(/verified-cell/);
  });

  test('Andariel Hell BK anchor = 1:4,080 @ 300MF (RoW)', async ({ page }) => {
    const row = page.locator('#andariel tr[data-item="Bul-Kathos Wedding Band"]');
    const hellCell = row.locator('td.diff-col').nth(4);
    await expect(hellCell).toContainText('1:4,080');
    await expect(hellCell).toHaveClass(/verified-cell/);
  });

  test('verified cells have lock icon tooltip', async ({ page }) => {
    const cell = page.locator('#mephisto tr[data-item="Harlequin Crest (Shako)"] td.diff-col').nth(4);
    await expect(cell).toHaveAttribute('title', /verified/i);
  });
});
