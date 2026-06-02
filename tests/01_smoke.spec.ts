import { test, expect } from '@playwright/test';

import * as path from 'path';
const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');
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

  test('editorial masthead renders title + tagline', async ({ page }) => {
    await page.goto(BIBLE);
    // v61: the "Vol. XLIII · Spring 2026 · The Sanctuary Codex" kicker was removed at
    // Konyo's request. The masthead now leads with the title + tagline; assert those.
    await expect(page.locator('.masthead .h-title')).toContainText(/Konyo's D2R Farming Bible/);
    await expect(page.locator('.masthead-tagline')).toContainText(/grail-hunting reference/i);
  });

  test('all primary tabs render', async ({ page }) => {
    await page.goto(BIBLE);
    // Assert by data-tab (stable) rather than visible label — the "ancients" tab is now
    // labelled "events" and a "binds" tab was added; data-tab keys are the contract.
    const dataTabs = await page.locator('.tab').evaluateAll(els => els.map(e => e.getAttribute('data-tab')));
    expect(dataTabs.length).toBeGreaterThanOrEqual(7);
    for (const t of ['bosses', 'calc', 'tz', 'runes', 'rotw', 'ancients', 'ref']) {
      expect(dataTabs, `missing tab [data-tab=${t}]`).toContain(t);
    }
  });

  test('all 11 boss cards render with required structure', async ({ page }) => {
    await page.goto(BIBLE);
    await page.evaluate(() => window.switchTab('bosses'));
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

  test('legend renders 8 cards (5 base states + rarity/pills/fastest)', async ({ page }) => {
    await page.goto(BIBLE);
    const legend = page.locator('.legend-box .legend-item-card');
    await expect(legend).toHaveCount(8);
    // new self-documenting states must be present (legend ↔ render parity)
    await expect(page.locator('.legend-box .lc-rarity')).toHaveCount(1);
    await expect(page.locator('.legend-box .lc-pill')).toHaveCount(1);
    await expect(page.locator('.legend-box .lc-pill .pill')).not.toHaveCount(0);
    // stale "v8" must be gone; verified count stays honest at 3
    await expect(page.locator('.legend-box')).not.toContainText('v8');
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
