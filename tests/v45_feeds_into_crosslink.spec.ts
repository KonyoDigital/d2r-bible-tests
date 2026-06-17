import { test, expect } from '@playwright/test';
import * as path from 'path';
import { BOSS_CHIPS_TOTAL, CALC_ITEMS_TOTAL } from './_data_locks';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v45 — event/material cross-link layer (CC 2026-06-01).
//  - Every TZ zone is clickable: tracked boss -> openBossDetail; super-unique-only zone -> inline drop detail.
//  - Each farm card shows a "what this farm feeds into" strip (keys / essences / shards / ancient statues).
//  - A keys/shards/essences reference section renders right under the grail (event-ref), NOT in the grail count.
//  - Canonical key attributions: Terror->Countess, Hate->Summoner, Destruction->Nihlathak.
test.describe('v45 feeds-into cross-link — zones clickable + keys/shards/essences reference', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('cross-link layer + helpers are exposed and integrity is unchanged', async ({ page }) => {
    const r = await page.evaluate(() => ({
      bosses: (eval('BOSSES') as any[]).length,
      items: (eval('ITEMS') as any[]).length,
      feedsKeys: Object.keys((window as any).zoneFeedsInto ? (eval('BOSS_FEEDS_INTO') as any) : {}).length,
      hasZoneFeedsInto: typeof (window as any).zoneFeedsInto,
      hasToggle: typeof (window as any).toggleZoneDetail,
      hasRenderEventRef: typeof (window as any).renderEventRef,
    }));
    expect(r.bosses).toBe(BOSS_CHIPS_TOTAL);
    expect(r.items).toBe(CALC_ITEMS_TOTAL); // grail count NOT inflated by event/material cross-links
    expect(r.feedsKeys).toBeGreaterThanOrEqual(8);
    expect(r.hasZoneFeedsInto).toBe('function');
    expect(r.hasToggle).toBe('function');
    expect(r.hasRenderEventRef).toBe('function');
  });

  test('every TZ zone card is clickable (onclick wired)', async ({ page }) => {
    const cards = page.locator('#tz-zones-container .tz-zone-card');
    const n = await cards.count();
    expect(n).toBeGreaterThanOrEqual(10);
    for (let i = 0; i < n; i++) {
      const oc = await cards.nth(i).getAttribute('onclick');
      expect(oc, `zone card ${i} must have a click handler`).toBeTruthy();
      expect(oc!).toMatch(/openBossDetail|toggleZoneDetail/);
    }
  });

  test('untracked super-unique zone toggles an inline drop detail', async ({ page }) => {
    // TZ zone cards live in the (non-default) "tz" tab — activate it so the inline detail
    // can actually become visible (its ancestor tab is display:none otherwise).
    await page.click('.tab[data-tab="tz"]');
    await page.waitForTimeout(200);
    // Find a zone card whose handler is toggleZoneDetail (no roster boss spawns there).
    const idx = await page.evaluate(() => {
      const cards = Array.from(document.querySelectorAll('#tz-zones-container .tz-zone-card'));
      return cards.findIndex(c => /toggleZoneDetail/.test(c.getAttribute('onclick') || ''));
    });
    expect(idx, 'at least one untracked super-unique zone should toggle inline detail').toBeGreaterThanOrEqual(0);
    const card = page.locator('#tz-zones-container .tz-zone-card').nth(idx);
    const detail = card.locator('.tz-zone-detail');
    await expect(detail).toBeHidden();
    // dispatchEvent fires the card's onclick wiring directly — verifies the toggle handler,
    // not a pixel hit-test (the sticky header / TZ countdown badge can intercept a physical click).
    await card.dispatchEvent('click');
    await page.waitForTimeout(200);
    await expect(detail).toBeVisible();
    await expect(detail).toContainText('feeds into');
  });

  test('boss detail card shows a "feeds into" strip for material-source bosses', async ({ page }) => {
    // setActiveBoss/openBossDetail renders the golden boss card into #boss-detail-panel.
    // Countess feeds Key of Terror (Uber Tristram). Mephisto feeds Hatred essence + ancient statue.
    await page.evaluate(() => (window as any).openBossDetail('countess'));
    await page.waitForTimeout(400);
    const countess = await page.evaluate(() => {
      const sec = document.getElementById('boss-detail-panel')?.querySelector('.feeds-into-strip');
      return sec ? sec.textContent : null;
    });
    expect(countess).toBeTruthy();
    expect(countess!).toContain('Key of Terror');

    await page.evaluate(() => (window as any).openBossDetail('mephisto'));
    await page.waitForTimeout(400);
    const meph = await page.evaluate(() => {
      const sec = document.getElementById('boss-detail-panel')?.querySelector('.feeds-into-strip');
      return sec ? sec.textContent : null;
    });
    expect(meph).toBeTruthy();
    expect(meph!).toMatch(/Hatred|Essence/i);
  });

  test('event-ref reference section renders under the grail with correct key attributions', async ({ page }) => {
    const er = page.locator('#event-ref');
    await expect(er).toBeVisible();
    // v63: dropdown sections default-collapsed → expand the er section to read its body
    await er.locator('.sec-h').click();
    // four reference blocks: keys, worldstone shards, essences, Token of Absolution (v106)
    const blocks = er.locator('.er-block');
    expect(await blocks.count()).toBe(4);
    const txt = (await er.innerText()).replace(/\s+/g, ' ');
    // canonical Pandemonium key -> boss attributions
    expect(txt).toMatch(/Key of Terror[\s\S]*Countess/);
    expect(txt).toMatch(/Key of Hate[\s\S]*Summoner/);
    expect(txt).toMatch(/Key of Destruction[\s\S]*Nihlathak/);
    // v106: the Token-of-Absolution block surfaces here too, feeding a respec (block head is
    // CSS-uppercased → match case-insensitively)
    expect(txt).toMatch(/Token of Absolution[\s\S]*Respec/i);
    // it is explicitly a cross-link, not part of the grail count
    expect(txt).toContain('not counted in the grail');
  });

  test('corrected key tooltips: no scrambled Hate->Nihlathak / Terror->Summoner mapping in rendered text', async ({ page }) => {
    // Use visible rendered text (body.innerText) — NOT documentElement.innerHTML, which would
    // also serialize <script> source where the BOSS_FEEDS_INTO object literal lists keys adjacent
    // to other boss ids (a false positive that has nothing to do with user-facing attributions).
    const bad = await page.evaluate(() => {
      const t = document.body.innerText;
      return {
        hateNihl: /Key of Hate[^\n]{0,40}Nihl/i.test(t),
        terrorSummoner: /Key of Terror[^\n]{0,40}Summoner/i.test(t),
        destructionCountess: /Key of Destruction[^\n]{0,40}Countess/i.test(t),
      };
    });
    expect(bad.hateNihl).toBe(false);
    expect(bad.terrorSummoner).toBe(false);
    expect(bad.destructionCountess).toBe(false);
  });
});
