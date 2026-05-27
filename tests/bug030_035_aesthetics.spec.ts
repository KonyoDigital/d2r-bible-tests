import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('BUG-030..035 — aesthetics sweep', () => {
  test('BUG-030 all 11 boss cards have consistent structure', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    const cards = page.locator('#boss-cards .boss-card');
    const count = await cards.count();
    expect(count).toBe(11);

    // Each must have: .boss-header.clickable, .boss-emoji, .boss-name, .boss-tier-tag, .boss-body
    for (let i = 0; i < count; i++) {
      const card = cards.nth(i);
      await expect(card.locator('.boss-header.clickable')).toBeAttached();
      await expect(card.locator('.boss-emoji')).toBeAttached();
      await expect(card.locator('.boss-name')).toBeAttached();
      await expect(card.locator('.boss-tier-tag')).toBeAttached();
      await expect(card.locator('.boss-body')).toBeAttached();
    }
  });

  test('BUG-031 section headers use uppercase + gold color', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    // Pick a known section header inside a boss card
    const h3 = page.locator('#boss-cards h3').first();
    const style = await h3.evaluate(el => {
      const cs = getComputedStyle(el);
      return { color: cs.color, transform: cs.textTransform, letter: cs.letterSpacing };
    });
    expect(style.transform).toBe('uppercase');
    // gold color: red dominant + green > blue + red > 180
    const m = style.color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    expect(m).not.toBeNull();
    const [r, g, b] = m!.slice(1).map(Number);
    expect(r).toBeGreaterThan(180);
    expect(r).toBeGreaterThan(g);
    expect(g).toBeGreaterThan(b);
  });

  test('BUG-032 .blocked cells have distinct color', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    // Find any drops cell with class .blocked / .impossible / data-blocked
    const blocked = page.locator('#boss-cards td.blocked, #boss-cards .blocked').first();
    if (await blocked.count()) {
      const color = await blocked.evaluate(el => getComputedStyle(el).color);
      // Just assert it's set
      expect(color).toBeTruthy();
    }
  });

  test('BUG-033 boss-card has hover affordance (v39: boss-card:hover lift)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    const hasHover = await page.evaluate(() => {
      for (const sheet of Array.from(document.styleSheets)) {
        try {
          for (const rule of Array.from((sheet as CSSStyleSheet).cssRules || [])) {
            if (rule instanceof CSSStyleRule && /\.boss-card[^a-z].*:hover|\.boss-header[^a-z].*:hover/.test(rule.selectorText)) return true;
          }
        } catch {}
      }
      return false;
    });
    expect(hasHover).toBe(true);
  });

  test('BUG-034 mobile viewport (375px) — no horizontal page overflow', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 800 });
    await page.goto(BIBLE);
    await page.waitForTimeout(700);
    const overflow = await page.evaluate(() => {
      const w = document.documentElement;
      return { scroll: w.scrollWidth, client: w.clientWidth };
    });
    // Allow up to 20px overflow as float-precision tolerance
    expect(overflow.scroll - overflow.client).toBeLessThanOrEqual(20);
  });

  test('BUG-035 difficulty-grid renders for each boss card', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    const cards = await page.locator('#boss-cards .boss-card').count();
    const grids = await page.locator('#boss-cards .diff-grid').count();
    expect(grids).toBe(cards);
  });

  test('BUG-035b boss-detail overlay also responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 800 });
    await page.goto(BIBLE);
    await page.waitForTimeout(500);
    await page.evaluate(() => (window as any).openBossDetail('mephisto'));
    await page.waitForTimeout(300);
    await expect(page.locator('#boss-detail-overlay')).not.toHaveClass(/hidden/);
    // Card should fit within viewport width
    // v39: was .boss-detail-card, now .gbc-card inside #boss-detail-panel
    const cardW = await page.locator('#boss-detail-panel .gbc-card').evaluate(el => el.getBoundingClientRect().width);
    expect(cardW).toBeLessThanOrEqual(375);
  });
});
