import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v55 — ROTW tab drop unification. The Worldstone Shards grid, Essences table,
// and Pandemonium Keys table showed drops as dead text (audit: 0 routes). Each
// item is now clickable → openDrop → the same #item-detail material card the
// rest of the site uses. Desktop restructured these sections into golden hub
// cards with .colossal-tile grids; each tile has onclick→openDrop and a .ct-name.
test.describe('v55 ROTW tab drop unification', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => (window as any).switchTab('rotw'));
  });

  test('a Worldstone Shard routes to its material card', async ({ page }) => {
    await page.locator('#tab-rotw .colossal-tile .ct-name', { hasText: 'Worldstone Shard (Western)' }).first().evaluate((e:any) => e.closest('.colossal-tile').click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Worldstone Shard');
    await expect(page.locator('#item-detail .material-card')).toContainText('Rotting Fissure'); // Western's Renewed target
  });

  test('an Essence routes to its material card (display→canonical map)', async ({ page }) => {
    await page.locator('#tab-rotw .colossal-tile .ct-name', { hasText: 'Charged Essence of Hatred' }).first().evaluate((e:any) => e.closest('.colossal-tile').click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Hatred');
  });

  test('a Pandemonium Key routes to its material card', async ({ page }) => {
    await page.locator('#tab-rotw .colossal-tile .ct-name', { hasText: 'Key of Destruction' }).first().evaluate((e:any) => e.closest('.colossal-tile').click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Key of Destruction');
  });

  test('all shard/essence/key/sunder tiles are wired via colossal-tile onclick (no dead text)', async ({ page }) => {
    // Desktop restructured all RotW drop sections into golden hub cards with
    // .colossal-tile grids. Each tile carries onclick→openDrop on the tile div.
    // 5 shards + 4 essences + 3 keys + 6 sunders = 18 routable tiles in the hubs,
    // plus 5 Herald tier tiles = 23 total .colossal-tile[onclick] in #tab-rotw.
    const wiredTiles = await page.locator('#tab-rotw .colossal-tile[onclick]').count();
    expect(wiredTiles).toBeGreaterThanOrEqual(18); // at least the 18 hub tiles
    // Verify the 5 shard tiles specifically exist with their names
    const shardNames = await page.locator('#rotw-ws-hub .colossal-tile .ct-name').allTextContents();
    expect(shardNames.filter(n => n.includes('Worldstone Shard')).length).toBe(5);
  });

  test('a Sunder Charm routes to its card with its exact Renewed recipe', async ({ page }) => {
    await page.locator('#tab-rotw .colossal-tile .ct-name', { hasText: 'Cold Rupture' }).first().evaluate((e:any) => e.closest('.colossal-tile').click());
    await expect(page.locator('#item-detail .material-card')).toHaveCount(1);
    await expect(page.locator('#item-detail .material-card')).toContainText('Cold Rupture');
    await expect(page.locator('#item-detail .material-card')).toContainText('Worldstone Shard (Eastern)');
  });

});
