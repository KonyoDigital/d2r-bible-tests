import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v57 — ref-tab Cube Recipes: the routable items (Uber keys, organs, Hellfire
// Torch — all have cards) now click through to the unified material cards. The
// rune-upgrade rows + P#-slider group labels have NO cards, so are intentionally
// left as plain text (no fabricated links). The organ test also proves the
// escaped-apostrophe onclick (openDrop('Mephisto\'s Brain')) parses correctly.
test.describe('v57 ref cube-recipe routing', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => (window as any).switchTab('ref'));
  });

  test('an Uber key routes to its material card', async ({ page }) => {
    await page.locator('#tab-ref .zd-item-click', { hasText: 'Key of Terror' }).first().evaluate((e:any) => e.click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Key of Terror');
  });

  test('an organ (apostrophe in name) routes correctly', async ({ page }) => {
    await page.locator('#tab-ref .zd-item-click', { hasText: "Mephisto's Brain" }).first().evaluate((e:any) => e.click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText("Mephisto's Brain");
  });

  test('Hellfire Torch routes to its card', async ({ page }) => {
    await page.locator('#tab-ref .zd-item-click', { hasText: 'Hellfire Torch' }).first().evaluate((e:any) => e.click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
  });
});
