import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('BUG-110..149 — discovery sweep (find next layer)', () => {
  test('BUG-110 rune drop table has ≥10 rows (mid-high runes)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('.tab[data-tab="runes"]').click();
    await page.waitForTimeout(200);
    const rows = await page.locator('#tab-runes tbody tr').count();
    expect(rows).toBeGreaterThanOrEqual(10);
  });

  test('BUG-111 every boss has all 6 difficulty columns', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    const cards = await page.locator('#boss-cards .boss-card').count();
    for (let i = 0; i < cards; i++) {
      const grids = await page.locator('#boss-cards .boss-card').nth(i).locator('.diff-grid .diff-card, .diff-grid > div').count();
      expect(grids).toBeGreaterThanOrEqual(6);
    }
  });

  test('BUG-112 every boss card drops table has ≥1 row', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    const cards = await page.locator('#boss-cards .boss-card').count();
    for (let i = 0; i < cards; i++) {
      const rows = await page.locator('#boss-cards .boss-card').nth(i).locator('table.drops tbody tr').count();
      expect(rows).toBeGreaterThanOrEqual(1);
    }
  });

  test('BUG-113 search-clear (empty fill) restores full grid', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('.tab[data-tab="calc"]').click();
    const before = await page.locator('#item-grid .item-tile:visible').count();
    await page.locator('#item-search').fill('xyznonsense');
    await page.waitForTimeout(200);
    const filtered = await page.locator('#item-grid .item-tile:visible').count();
    expect(filtered).toBeLessThan(before);
    await page.locator('#item-search').fill('');
    await page.waitForTimeout(200);
    const after = await page.locator('#item-grid .item-tile:visible').count();
    expect(after).toBe(before);
  });

  test('BUG-114 set-piece toggle adds CSS class', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('.tab[data-tab="rotw"]').click();
    await page.waitForTimeout(200);
    const piece = page.locator('.set-piece').first();
    if (await piece.count()) {
      const before = await piece.getAttribute('class');
      await piece.click();
      await page.waitForTimeout(150);
      const after = await piece.getAttribute('class');
      expect(before).not.toBe(after);
    }
  });

  test('BUG-115 MF math: effective MF formula matches diminishing returns', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    // effMF(300, 250) = 300*100/(300+250) = 54.5%
    const eff = await page.evaluate(() => (window as any).effMF ? (window as any).effMF(300, 250) : null);
    if (eff !== null) {
      expect(eff).toBeCloseTo(54.5, 0);
    }
  });

  test('BUG-116 reset button confirms and reloads (no auto-trigger)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    // Set a wishlist item, hit reset (with cancel) — wishlist preserved
    await page.evaluate(() => {
      localStorage.setItem('d2r_wishlist', JSON.stringify(['Test Item']));
    });
    page.on('dialog', d => d.dismiss());
    const btn = page.locator('.reset-btn').first();
    if (await btn.count()) {
      await btn.click().catch(() => {});
      await page.waitForTimeout(200);
    }
    const wish = await page.evaluate(() => JSON.parse(localStorage.getItem('d2r_wishlist') || '[]'));
    expect(wish).toContain('Test Item');
  });

  test('BUG-117 hero card updates after MF change', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    const before = await page.locator('.hero, #hero, [class*="hero"]').first().innerText();
    await page.evaluate(() => {
      const s = document.getElementById('mf') as HTMLInputElement;
      s.value = '1000'; s.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await page.waitForTimeout(300);
    const after = await page.locator('.hero, #hero, [class*="hero"]').first().innerText();
    expect(before).not.toBe(after);
  });

  test('BUG-118 filter pill "all" returns full grid', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('.tab[data-tab="calc"]').click();
    const total = await page.locator('#item-grid .item-tile').count();
    const grailPill = page.locator('.filter-pill[data-filter="grail"]');
    if (await grailPill.count()) {
      await grailPill.click();
      await page.waitForTimeout(200);
      await page.locator('.filter-pill[data-filter="all"]').click();
      await page.waitForTimeout(200);
      const after = await page.locator('#item-grid .item-tile:visible').count();
      expect(after).toBe(total);
    }
  });

  test('BUG-119 sort persists across renders', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    const hdr = page.locator('#countess th.sortable').first();
    if (await hdr.count()) {
      await hdr.click();
      await page.waitForTimeout(150);
      const cls1 = await hdr.getAttribute('class');
      // Trigger re-render (toggle filter)
      await page.evaluate(() => {
        const fn = (window as any).setBossFilter;
        if (fn) fn('countess', 'grail');
        if (fn) fn('countess', 'all');
      });
      await page.waitForTimeout(200);
      const cls2 = await page.locator('#countess th.sortable').first().getAttribute('class');
      expect(cls2).toContain('sort-');
    }
  });

  test('BUG-120 boss detail opens for all 11 bosses without error', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    const ids = ['countess','andariel','duriel','mephisto','travincal','diablo','baal','pindle','nihl','cows','pit'];
    for (const id of ids) {
      await page.evaluate((bossId) => (window as any).openBossDetail(bossId), id);
      await page.waitForTimeout(80);
      const cls = await page.evaluate(() => document.getElementById('boss-detail-overlay')?.className);
      expect(cls).not.toMatch(/hidden/);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(80);
    }
    expect(errors).toEqual([]);
  });

  test('BUG-121 boss-nav has exactly 11 chips', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    const chips = await page.locator('#boss-nav .boss-chip').count();
    expect(chips).toBe(11);
  });

  test('BUG-122 TZ tab has ≥10 zones', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(200);
    const zones = await page.locator('.tz-zone-card').count();
    expect(zones).toBeGreaterThanOrEqual(10);
  });

  test('BUG-123 RotW statues ≥5', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.locator('.tab[data-tab="rotw"]').click();
    await page.waitForTimeout(200);
    const statues = await page.locator('#statue-tracker > div').count();
    expect(statues).toBeGreaterThanOrEqual(5);
  });

  test('BUG-124 detail overlay closes when opening another boss', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.evaluate(() => (window as any).openBossDetail('pit'));
    await page.waitForTimeout(150);
    const nameA = await page.locator('.boss-detail-header .bd-name').innerText();
    await page.evaluate(() => (window as any).openBossDetail('mephisto'));
    await page.waitForTimeout(150);
    const nameB = await page.locator('.boss-detail-header .bd-name').innerText();
    expect(nameA.toLowerCase()).toContain('pit');
    expect(nameB.toLowerCase()).toContain('mephisto');
  });
});
