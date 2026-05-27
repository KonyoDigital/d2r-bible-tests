import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible_routes.html');

test.describe('BUG-010 — universal boss detail panel', () => {
  test('clicking boss-header opens overlay with correct boss name', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('#pit .boss-header').click();
    await page.waitForTimeout(200);
    const overlay = page.locator('#boss-detail-overlay');
    await expect(overlay).toBeVisible();
    await expect(overlay).not.toHaveClass(/hidden/);
    const name = await page.locator('.boss-detail-header .bd-name').innerText();
    expect(name.toLowerCase()).toContain('pit');
  });

  test('detail card renders all 6 difficulty cells', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('#mephisto .boss-header').click();
    await page.waitForTimeout(200);
    // v39: was .bd-diff-cell, now .gbc-diff-cell
    const cells = await page.locator('.gbc-diff-cell').count();
    expect(cells).toBe(6);
  });

  test('Escape key closes overlay', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('#andariel .boss-header').click();
    await page.waitForTimeout(200);
    await expect(page.locator('#boss-detail-overlay')).toBeVisible();
    await page.keyboard.press('Escape');
    await page.waitForTimeout(200);
    await expect(page.locator('#boss-detail-overlay')).toHaveClass(/hidden/);
  });

  test('close button (×) closes overlay', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('#countess .boss-header').click();
    await page.waitForTimeout(200);
    // v39: was .boss-detail-close, now .gbc-close (✕ close button)
    await page.evaluate(() => {
      const btn = document.querySelector('.gbc-close') as HTMLElement;
      btn?.click();
    });
    await page.waitForTimeout(200);
    await expect(page.locator('#boss-detail-overlay')).toHaveClass(/hidden/);
  });

  test('clearActiveBoss() programmatic close hides overlay', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('#diablo .boss-header').click();
    await page.waitForTimeout(200);
    await expect(page.locator('#boss-detail-overlay')).not.toHaveClass(/hidden/);
    // v39 deliberately removed backdrop-click-to-close; programmatic close path remains
    await page.evaluate(() => (window as any).clearActiveBoss?.());
    await page.waitForTimeout(200);
    await expect(page.locator('#boss-detail-overlay')).toHaveClass(/hidden/);
  });

  test('boss-nav chip click opens boss-detail overlay (v39 behavior)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    // v39: boss-nav chip calls setActiveBoss() which opens the overlay
    // (was: scroll+flash on boss-card header in v12).
    const chip = page.locator('#boss-nav .boss-chip[data-boss-id="mephisto"]');
    await chip.click();
    await page.waitForTimeout(250);
    await expect(page.locator('#boss-detail-overlay')).not.toHaveClass(/hidden/);
    const name = await page.locator('#boss-detail-panel .bd-name').innerText();
    expect(name.toLowerCase()).toContain('meph');
  });

  test('top drops table renders ≥1 row', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('#mephisto .boss-header').click();
    await page.waitForTimeout(200);
    // v39: top drops table renders inside .gbc-card (was .boss-detail-body)
    const rows = await page.locator('#boss-detail-panel .gbc-card table.drops tbody tr').count();
    expect(rows).toBeGreaterThanOrEqual(1);
  });

  test('detail "open full boss card" button closes overlay + scrolls', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('#baal .boss-header').click();
    await page.waitForTimeout(200);
    // v39: was .bd-action-btn.primary, now the bottom .gbc-close ("↓ scroll to full filterable drop table")
    await page.locator('#boss-detail-panel .gbc-close', { hasText: 'scroll' }).click();
    await page.waitForTimeout(300);
    await expect(page.locator('#boss-detail-overlay')).toHaveClass(/hidden/);
    await expect(page.locator('#baal')).toBeVisible();
  });

  test('no console errors after opening + closing 3 different bosses', async ({ page }) => {
    const errors: string[] = [];
    // v41 routine_status.js sibling-path 404 is an expected graceful-fallback emission, not a bug.
    const isBenign = (m: string) => /routine_status\.js/i.test(m) || /Failed to load resource.*ERR_FILE_NOT_FOUND/i.test(m);
    page.on('pageerror', e => errors.push('pageerror: ' + e.message));
    page.on('console', m => { if (m.type() === 'error' && !isBenign(m.text())) errors.push('console.error: ' + m.text()); });
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    for (const id of ['pit', 'mephisto', 'andariel']) {
      await page.locator(`#${id} .boss-header`).click();
      await page.waitForTimeout(150);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(150);
    }
    if (errors.length) console.log('ERRORS:', errors);
    expect(errors).toEqual([]);
  });
});
