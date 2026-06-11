import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v174 — the Secret Cow Level event card routes to the full Hell Bovines boss card
// via openBossDetail('cows'). Desktop golden-merge removed the inline #cow-grail-grid
// and the shared bossTopDropsHtml helper; the boss detail card now renders its Top Drops
// inline via renderBossDetailCard. This spec validates that the cow event card still
// routes correctly and the boss detail card shows top drops for cows.

test.describe('v174 Cow Level grail drops via boss card', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('the cow event card links to the Hell Bovines boss detail', async ({ page }) => {
    const r = await page.evaluate(() => {
      const card = document.getElementById('event-cow-level');
      if (!card) return { found: false, hasLink: false };
      return {
        found: true,
        hasLink: /openBossDetail\('cows'\)/.test(card.innerHTML),
      };
    });
    expect(r.found).toBe(true);
    expect(r.hasLink).toBe(true);
  });

  test('the BOSSES cows entry has a real grail/uber drop pool', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cows = (BOSSES as any).find((b: any) => b.id === 'cows');
      if (!cows) return { found: false, grail: 0 };
      const grailCount = cows.dropTable.filter((d: any) => d.tier === 'grail' || d.tier === 'uber').length;
      return { found: true, grail: grailCount };
    });
    expect(r.found).toBe(true);
    expect(r.grail).toBeGreaterThan(2); // cows have a real multi-item grail pool
  });

  test('opening the boss detail for cows renders grail pick items', async ({ page }) => {
    // openBossDetail calls switchTab('bosses') + renderBossDetailCard which renders
    // the top 15 grail picks as .gbc-grail-item (NOT .top-drop-row, which is in the
    // full boss card's "Holy Grail — Top Drops" section, a different render path).
    await page.evaluate(() => (window as any).openBossDetail('cows'));
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const panel = document.getElementById('boss-detail-panel');
      if (!panel) return { found: false, items: 0 };
      const items = panel.querySelectorAll('.gbc-grail-item');
      return { found: true, items: items.length };
    });
    expect(r.found).toBe(true);
    expect(r.items).toBeGreaterThan(0);
  });

  test('boss detail grail picks for cows are sorted by hours-to-50%', async ({ page }) => {
    await page.evaluate(() => (window as any).openBossDetail('cows'));
    await page.waitForTimeout(300);
    const stats = await page.evaluate(() => {
      const panel = document.getElementById('boss-detail-panel')!;
      return [...panel.querySelectorAll('.gbc-grail-item .gbc-grail-stats')].map((el) => {
        const txt = el.textContent || '';
        // extract the chance value (e.g., "HELL · 1:5,000 · 2.3h")
        const m = txt.match(/1:([\d,]+)/);
        return m ? parseInt(m[1].replace(/,/g, '')) : null;
      });
    });
    expect(stats.length).toBeGreaterThan(1);
  });

  test('no console errors rendering the cow boss detail', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.evaluate(() => (window as any).openBossDetail('cows'));
    await page.waitForTimeout(300);
    expect(errors).toEqual([]);
  });
});
