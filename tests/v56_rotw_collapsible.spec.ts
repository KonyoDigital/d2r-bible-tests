import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v56 — ROTW data sections are collapsible via the generic toggleSec mechanism.
// The 4 data sections (Shards/Essences/Keys/Sunders) get a clickable .sec-h
// header + .sec-body wrapper, default-expanded. The 2 interactive trackers
// (Statues, Set) are intentionally left untouched.
test.describe('v56 ROTW collapsible sections', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => (window as any).switchTab('rotw'));
  });

  test('4 data sections collapsible, expanded by default', async ({ page }) => {
    await expect(page.locator('#tab-rotw .sec-h')).toHaveCount(4);
    await expect(page.locator('#tab-rotw .sec-body')).toHaveCount(4);
    await expect(page.locator('#tab-rotw .sec-body[hidden]')).toHaveCount(0);
  });

  test('clicking a header collapses, clicking again expands', async ({ page }) => {
    const head = page.locator('#tab-rotw .sec-h', { hasText: 'Worldstone Shards' });
    const body = head.locator('xpath=following-sibling::div[1]');
    await head.evaluate((e:any) => e.click());
    await expect(body).toBeHidden();
    await head.evaluate((e:any) => e.click());
    await expect(body).toBeVisible();
  });

  test('routing still works inside a wrapped section', async ({ page }) => {
    await page.locator('#tab-rotw .shard-name.zd-item-click', { hasText: 'Eastern Worldstone Shard' }).first().evaluate((e:any) => e.click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Cold Rupture');
  });

  test('statue tracker cross-links to the Colossal Ancient Jewels card', async ({ page }) => {
    await page.locator('#tab-rotw .zd-item-click', { hasText: 'Colossal Ancient Jewels' }).first().evaluate((e:any) => e.click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Colossal Ancient Jewels');
  });

});
