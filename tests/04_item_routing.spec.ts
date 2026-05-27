import { test, expect } from '@playwright/test';
import * as path from 'path';
const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible_routes.html');

// v38 selector map (was v12):
//   .detail-name      -> .aid-item-name
//   .source-strip     -> .aid-tabbar-chips (chips inside aid-card)
//   .source-chip      -> .source-chip (still used inside .aid-tabbar-chips)
//   .pin-btn          -> first .aid-tabbar-chips .source-chip click
//                        (calls setActiveItem + switchTab('bosses') in calc context)
//   .best-source-box  -> .best-source-box (unchanged)
//   .has-item/.no-item -> unchanged (set by setActiveItem on .boss-card)

test.describe('Item click routing — v38 (was v12 sharpness)', () => {
  test('clicking item in boss table jumps to calculator detail', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    const row = page.locator('#mephisto tr[data-item="Harlequin Crest (Shako)"]');
    await row.locator('td.item-name').click();
    await expect(page.locator('.tab[data-tab="calc"]')).toHaveClass(/active/);
    await expect(page.locator('#item-detail')).toHaveClass(/show/);
    await expect(page.locator('#item-detail .aid-item-name')).toContainText('Harlequin Crest (Shako)');
  });

  test('detail panel shows multiple jump chips', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    await page.click('.tab[data-tab="calc"]');
    await page.fill('#item-search', 'shako');
    await page.waitForTimeout(150);
    await page.locator('.item-tile').first().click();
    await page.waitForTimeout(150);
    const chips = page.locator('#item-detail .aid-tabbar-chips .source-chip');
    const count = await chips.count();
    expect(count, 'Shako should have multiple sources').toBeGreaterThan(3);
  });

  test('clicking source chip jumps to boss + activates item bar', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    await page.click('.tab[data-tab="calc"]');
    await page.fill('#item-search', 'shako');
    await page.waitForTimeout(150);
    await page.locator('.item-tile').first().click();
    await page.waitForTimeout(150);
    const firstChip = page.locator('#item-detail .aid-tabbar-chips .source-chip').first();
    await firstChip.click();
    await page.waitForTimeout(300);
    await expect(page.locator('.tab[data-tab="bosses"]')).toHaveClass(/active/);
    await expect(page.locator('#active-item-bar')).toHaveClass(/show/);
    await expect(page.locator('#aib-item-name')).toContainText('Shako');
  });

  test('active item glows on bosses that drop it, dims others', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    await page.click('.tab[data-tab="calc"]');
    await page.fill('#item-search', 'tyrael');
    await page.waitForTimeout(150);
    await page.locator('.item-tile').first().click();
    await page.waitForTimeout(150);
    // Click first source-chip in aid-card — this calls setActiveItem + switchTab('bosses')
    await page.locator('#item-detail .aid-tabbar-chips .source-chip').first().click();
    await page.waitForTimeout(400);
    await expect(page.locator('.tab[data-tab="bosses"]')).toHaveClass(/active/);
    // Tyrael's drops from Diablo, Baal (TC87+). Mephisto/Countess can never reach it (TC78 ceiling).
    await expect(page.locator('#diablo')).toHaveClass(/has-item/);
    await expect(page.locator('#baal')).toHaveClass(/has-item/);
    await expect(page.locator('#mephisto')).toHaveClass(/no-item/);
    await expect(page.locator('#countess')).toHaveClass(/no-item/);
  });

  test('Esc clears active item', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    await page.click('.tab[data-tab="calc"]');
    await page.fill('#item-search', 'stone of jordan');
    await page.waitForTimeout(200);
    await page.locator('.item-tile').first().click();
    await page.waitForTimeout(200);
    await page.locator('#item-detail .aid-tabbar-chips .source-chip').first().click();
    await page.waitForTimeout(300);
    await expect(page.locator('#active-item-bar')).toHaveClass(/show/);
    // defocus #item-search before Escape so search field doesn't swallow the key
    await page.locator('body').click({ position: { x: 5, y: 5 }});
    await page.waitForTimeout(100);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(200);
    await expect(page.locator('#active-item-bar')).not.toHaveClass(/show/);
  });

  test('aid-card "jump to boss" button jumps to bosses tab', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(400);
    await page.click('.tab[data-tab="calc"]');
    await page.fill('#item-search', 'shako');
    await page.waitForTimeout(200);
    await page.locator('.item-tile').first().click();
    await page.waitForTimeout(200);
    // v38: bestBoxHtml is computed but unused; aid-card "↗ jump to boss" is the v38-equivalent
    await page.locator('#item-detail .aid-close-btn', { hasText: 'jump to boss' }).click();
    await page.waitForTimeout(300);
    await expect(page.locator('.tab[data-tab="bosses"]')).toHaveClass(/active/);
  });

  test('hero card pick clicks open item detail', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(600);
    const firstPick = page.locator('.hero-pick').first();
    await expect(firstPick).toBeVisible();
    await firstPick.click();
    await page.waitForTimeout(300);
    // v38: hero-pick opens Golden Item Card at top of page (openItemDetail).
    // We start on bosses tab; clicking a hero-pick does not change tab.
    await expect(page.locator('.tab[data-tab="bosses"]')).toHaveClass(/active/);
    await expect(page.locator('#item-detail-panel')).not.toHaveClass(/hidden/);
    await expect(page.locator('#item-detail-panel .gic-card')).toBeVisible();
  });
});
