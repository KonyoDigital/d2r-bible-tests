import { test, expect } from '@playwright/test';
import * as path from 'path';

const BIBLE = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// CC 2026-06-01 unify: every TZ zone is now its own droppable ID card. Clicking ANY
// zone (including roster-boss zones like WSK→baal, Catacombs→andariel) opens its OWN
// inline drop detail instead of jumping straight to the boss overlay; the boss card is
// surfaced as a "full drop table →" cross-link INSIDE that detail (one canonical boss
// card, linked everywhere). data-boss-id stays populated for the affordance/lockdown probes.
test.describe('BUG-013 — TZ-zone droppable ID card + boss cross-link', () => {
  test('Catacombs L4 card opens its OWN inline detail, with an andariel full-table cross-link that opens the boss', async ({ page }) => {
    await page.goto(BIBLE);
    await page.waitForTimeout(1200);
    await page.locator('.tab[data-tab="tz"]').click();
    await page.waitForTimeout(300);
    const card = page.locator('.tz-zone-card[data-boss-id="andariel"]').first();
    await card.scrollIntoViewIfNeeded();
    await expect(card).toBeVisible();
    // click the zone card → its own inline drop detail opens (NOT the boss overlay)
    await page.evaluate(() => {
      const el = document.querySelector('.tz-zone-card[data-boss-id="andariel"]') as HTMLElement;
      el?.click();
    });
    await page.waitForTimeout(300);
    const detail = card.locator('.tz-zone-detail');
    await expect(detail).toBeVisible();
    await expect(page.locator('#boss-detail-overlay')).toHaveClass(/hidden/); // not jumped yet
    // the detail carries the canonical boss cross-link
    const link = detail.locator('.su-tz-link', { hasText: /full drop table/ });
    await expect(link).toBeVisible();
    await link.click();
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
  test('every MAPPED TZ zone opens its own inline detail carrying a faithful boss cross-link (curated, not 100%)', async ({ page }) => {
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
    expect(data.mapped.length, 'the genuine zones (WSK, Halls, RoF, Catacombs…) must still cross-link a boss').toBeGreaterThan(0);
    for (const c of data.mapped) {
      expect(data.validIds, `zone "${c.name}" mapped to unknown boss "${c.bossId}"`).toContain(c.bossId);
      // click the zone card → its own inline detail opens with a boss cross-link whose
      // onclick targets exactly that bossId (one canonical boss card, linked here).
      const probe = await page.evaluate((idx) => {
        document.querySelectorAll('.tz-zone-detail').forEach(b => { b.setAttribute('hidden', ''); });
        const card = document.querySelectorAll('.tz-zone-card')[idx] as HTMLElement;
        card?.click();
        const detail = card?.querySelector('.tz-zone-detail') as HTMLElement;
        const link = detail && !detail.hasAttribute('hidden')
          ? Array.from(detail.querySelectorAll('.su-tz-link')).find(l => /full drop table/.test(l.textContent || ''))
          : null;
        return {
          detailOpen: !!detail && !detail.hasAttribute('hidden'),
          linkAttr: link ? (link.getAttribute('onclick') || '') : '',
        };
      }, c.i);
      expect(probe.detailOpen, `zone "${c.name}" must open its own inline detail on click`).toBe(true);
      expect(probe.linkAttr, `zone "${c.name}" detail must cross-link boss "${c.bossId}"`).toContain(`openBossDetail('${c.bossId}')`);
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
    // find any source-chip in the detail (v87: NORM/NM chips are render-hidden Hell-only —
    // target the first VISIBLE chip, which is the real post-hide user experience)
    const chip = page.locator('#item-detail .source-chip:visible').first();
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
    await page.locator('#item-detail .source-chip:visible').first().click();
    await page.waitForTimeout(300);
    // Should be on bosses tab now, NOT detail overlay
    await expect(page.locator('#boss-detail-overlay')).toHaveClass(/hidden/);
    await expect(page.locator('#tab-bosses')).toBeVisible();
  });
});
