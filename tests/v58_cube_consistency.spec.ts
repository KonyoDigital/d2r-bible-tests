import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v58 — cube-recipe item refs are now clickable consistently across tabs.
// The ancients (Uber Tristram event) organ cube-input routes like ref's. The
// rotw keys are clickable via the Pandemonium Keys table (v55) and ancients
// torch via the v54 event special-drops, so this closes the last cube gap.
test.describe('v58 cross-tab cube consistency', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('ancients cube-input organ routes to its card', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab('ancients'));
    const chip = page.locator('#tab-ancients .cube-input .zd-item-click', { hasText: "Mephisto's Brain" });
    await expect(chip).toHaveCount(1);
    await chip.first().evaluate((e:any) => e.click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText("Mephisto's Brain");
  });
});
