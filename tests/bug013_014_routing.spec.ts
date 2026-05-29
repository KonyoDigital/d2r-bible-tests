import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('BUG-013 — TZ-zone → boss detail routing', () => {
  test('Catacombs L4 TZ card has data-boss-id="andariel" and opens detail on click', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1200);
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(300);
    const card = page.locator('.tz-zone-card[data-boss-id="andariel"]').first();
    await card.scrollIntoViewIfNeeded();
    await expect(card).toBeVisible();
    // Use evaluate-click to bypass any Playwright stability interference
    await page.evaluate(() => {
      const el = document.querySelector('.tz-zone-card[data-boss-id="andariel"]') as HTMLElement;
      el?.click();
    });
    await page.waitForTimeout(400);
    await expect(page.locator('#boss-detail-overlay')).not.toHaveClass(/hidden/);
    const name = await page.locator('.boss-detail-header .bd-name').innerText();
    expect(name.toLowerCase()).toContain('andariel');
  });

  test('Halls of Anguish maps to nihl', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1200);
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(300);
    const card = page.locator('.tz-zone-card[data-boss-id="nihl"]').first();
    await expect(card).toBeVisible();
  });

  test('Worldstone Keep maps to baal', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1200);
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(300);
    const card = page.locator('.tz-zone-card[data-boss-id="baal"]').first();
    await expect(card).toBeVisible();
  });

  test('River of Flame maps to diablo', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1200);
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(300);
    const card = page.locator('.tz-zone-card[data-boss-id="diablo"]').first();
    await expect(card).toBeVisible();
  });

  // v44 routing-accuracy correction: the old "v39: 100% routed" rule was WRONG —
  // it forced super-unique-only zones (Crystalline Passage→Frozenstein, Tristram→
  // Griswold, Arcane Sanctuary→Summoner, etc.) to proxy onto a same-act boss, which
  // is exactly the mis-route Konyo reported. The correct invariant is CURATED routing:
  // a zone is mapped ONLY when a card-backed boss genuinely spawns there, and every
  // mapped card must open EXACTLY that boss. Whether the 6 super-unique zones are
  // unmapped is asserted separately (routing_and_data_integrity.spec.ts acceptance gate).
  test('every MAPPED TZ zone card routes faithfully to a valid boss (curated, not 100%)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1500);
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(300);
    const data = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll('.tz-zone-card'));
      return {
        total: cards.length,
        validIds: (BOSSES as any[]).map(b => b.id),
        mapped: cards.map((c, i) => ({
          i,
          name: (c.querySelector('.tz-zone-name')?.textContent || '').trim(),
          bossId: c.getAttribute('data-boss-id') || '',
        })).filter(c => c.bossId),
      };
    });
    expect(data.total).toBeGreaterThan(0);
    expect(data.mapped.length, 'the genuine zones (WSK, Halls, RoF, Catacombs…) must still route').toBeGreaterThan(0);
    for (const c of data.mapped) {
      expect(data.validIds, `zone "${c.name}" mapped to unknown boss "${c.bossId}"`).toContain(c.bossId);
      await page.evaluate(() => { if ((window as any).clearActiveBoss) (window as any).clearActiveBoss(); });
      await page.evaluate((idx) => { (document.querySelectorAll('.tz-zone-card')[idx] as HTMLElement)?.click(); }, c.i);
      await page.waitForTimeout(180);
      const active = await page.evaluate(() => eval('typeof activeBossId!=="undefined"?activeBossId:null'));
      expect(active, `zone "${c.name}" must open boss "${c.bossId}", opened "${active}"`).toBe(c.bossId);
    }
  });
});

test.describe('BUG-014 — Cmd/Ctrl-click source-chip opens boss detail', () => {
  test('Cmd-click on first source chip opens detail panel', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1200);
    await page.locator('.tab[data-tab="calc"]').click();
    await page.locator('#item-search').fill('nagel');
    await page.waitForTimeout(300);
    await page.locator('#item-grid .item-tile:visible').first().click();
    await page.waitForTimeout(300);
    // find any source-chip in the detail
    const chip = page.locator('#item-detail .source-chip').first();
    await expect(chip).toBeVisible();
    await chip.click({ modifiers: ['Meta'] });
    await page.waitForTimeout(400);
    await expect(page.locator('#boss-detail-overlay')).not.toHaveClass(/hidden/);
  });

  test('plain click on source chip still jumps to boss card (not detail)', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1200);
    await page.locator('.tab[data-tab="calc"]').click();
    await page.locator('#item-search').fill('nagel');
    await page.waitForTimeout(300);
    await page.locator('#item-grid .item-tile:visible').first().click();
    await page.waitForTimeout(300);
    await page.locator('#item-detail .source-chip').first().click();
    await page.waitForTimeout(300);
    // Should be on bosses tab now, NOT detail overlay
    await expect(page.locator('#boss-detail-overlay')).toHaveClass(/hidden/);
    await expect(page.locator('#tab-bosses')).toBeVisible();
  });
});
