import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v55 — ROTW tab drop unification. The Worldstone Shards grid, Essences table,
// and Pandemonium Keys table showed drops as dead text (audit: 0 routes). Each
// item is now clickable → openDrop → the same #item-detail material card the
// rest of the site uses. (Clicks fire the wired onclick directly; pixel-clicks
// are flaky only because a sticky page .header overlaps content scrolled to y=0,
// a layout artifact unrelated to the wiring — verified via elementFromPoint.)
test.describe('v55 ROTW tab drop unification', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => (window as any).switchTab('rotw'));
  });

  test('a Worldstone Shard routes to its material card', async ({ page }) => {
    await page.locator('#tab-rotw .shard-name.zd-item-click', { hasText: 'Worldstone Shard (Western)' }).first().evaluate((e:any) => e.click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Worldstone Shard');
    await expect(page.locator('#item-detail .material-card')).toContainText('Rotting Fissure'); // Western's Renewed target
  });

  test('an Essence routes to its material card (display→canonical map)', async ({ page }) => {
    await page.locator('#tab-rotw .zd-item-click', { hasText: 'Charged Essence of Hatred' }).first().evaluate((e:any) => e.click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Hatred');
  });

  test('a Pandemonium Key routes to its material card', async ({ page }) => {
    await page.locator('#tab-rotw .zd-item-click', { hasText: 'Key of Destruction' }).first().evaluate((e:any) => e.click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Key of Destruction');
  });

  test('all 5 shard cards + every essence/key cell are wired (no dead text)', async ({ page }) => {
    await expect(page.locator('#tab-rotw .shard-name')).toHaveCount(5);
    await expect(page.locator('#tab-rotw .shard-name.zd-item-click')).toHaveCount(5);
    await expect(page.locator('#tab-rotw td.item-name.zd-item-click')).toHaveCount(13); // 4 essences + 3 keys + 6 sunders
  });

  test('a Sunder Charm routes to its card with its exact Renewed recipe', async ({ page }) => {
    await page.locator('#tab-rotw .zd-item-click', { hasText: 'Cold Rupture' }).first().evaluate((e:any) => e.click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Cold Rupture');
    await expect(page.locator('#item-detail .material-card')).toContainText('Worldstone Shard (Eastern)');
  });

});
