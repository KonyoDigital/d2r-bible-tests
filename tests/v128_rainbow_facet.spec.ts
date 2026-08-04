import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v128 — Rainbow Facets modelled exactly like COLOSSAL_JEWELS: 8 descriptive,
// clickable ID cards (4 elements x 2 triggers) routed via openDrop() + searchable.
// VERIFIED ART ONLY (diablo2.io jewel sprites, HTTP 200 image/png 2026-06-08).
// Deliberately NO roll percentages and NO drop odds — Konyo plays Reign of the
// Warlock and no verified RotW facet stat/odds source exists, so stating either
// would be fabrication. Pure additive enrichment + routing layer.
test.describe('v128 Rainbow Facet descriptive cards (no odds, no roll %s)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  const FACETS = [
    'Rainbow Facet: Fire Level-up', 'Rainbow Facet: Fire Death',
    'Rainbow Facet: Cold Level-up', 'Rainbow Facet: Cold Death',
    'Rainbow Facet: Lightning Level-up', 'Rainbow Facet: Lightning Death',
    'Rainbow Facet: Poison Level-up', 'Rainbow Facet: Poison Death',
  ];

  test('all 8 facets exist in RAINBOW_FACETS and each has a verified _graphic.png in D2IO_ART', async ({ page }) => {
    const r = await page.evaluate((names) => {
      const facets = (window as any).RAINBOW_FACETS as any[];
      const art = (window as any).D2IO_ART;
      const labels = facets.map((f) => f.n);
      const missingData = names.filter((n) => !labels.includes(n));
      const badArt = names.filter((n) => !/^art\/.*_graphic\.png(?:\?|$)/.test(art[n] || ''));
      return { count: facets.length, missingData, badArt };
    }, FACETS);
    expect(r.count).toBe(8);
    expect(r.missingData).toEqual([]);
    expect(r.badArt).toEqual([]);
  });

  test('openDrop renders a rainbow-facet-card with art + affix structure and NO numeric roll/odds', async ({ page }) => {
    const r = await page.evaluate((names) => {
      const out: Record<string, { hasCard: boolean; hasImg: boolean; lazy: boolean; text: string }> = {};
      for (const n of names) {
        (window as any).openDrop(n);
        const card = document.querySelector('#item-detail .rainbow-facet-card') as HTMLElement | null;
        const img = card?.querySelector('.d2art-img') as HTMLImageElement | null;
        out[n] = {
          hasCard: !!card,
          hasImg: !!img,
          lazy: img?.getAttribute('loading') === 'lazy',
          text: card?.textContent || '',
        };
      }
      return out;
    }, FACETS);
    for (const n of FACETS) {
      expect(r[n].hasCard, `${n} renders a card`).toBe(true);
      expect(r[n].hasImg, `${n} has art img`).toBe(true);
      expect(r[n].lazy, `${n} img is lazy`).toBe(true);
      // dual-affix structure present (skill damage + enemy resistance)
      expect(r[n].text).toContain('Skill Damage');
      expect(r[n].text).toContain('Enemy');
      // ZERO FABRICATION: no fabricated roll %s or 1:N odds anywhere on the card.
      // (The only '%' allowed is in the affix-structure placeholders like "+% to".)
      expect(r[n].text).not.toMatch(/\d+%/);
      expect(r[n].text).not.toMatch(/1:\d/);
    }
  });

  test('the showcase renders a Rainbow Facets group with all 8 clickable tiles', async ({ page }) => {
    const r = await page.evaluate(() => {
      const box = document.getElementById('colossal-showcase');
      if (!box) return { mounted: false, tileCount: 0, heads: '' };
      (window as any).renderColossalShowcase();
      const heads = Array.from(box.querySelectorAll('.cs-group-head')).map((h) => h.textContent || '').join(' | ');
      const facetTiles = Array.from(box.querySelectorAll('.colossal-tile')).filter((t) =>
        (t.textContent || '').includes('Rainbow Facet:'));
      return { mounted: true, tileCount: facetTiles.length, heads };
    });
    expect(r.mounted).toBe(true);
    expect(r.heads).toContain('Rainbow Facets');
    expect(r.tileCount).toBe(8);
  });

  test('typing "rainbow facet" in the global search surfaces facet results (live index)', async ({ page }) => {
    const input = page.locator('#gsearch-input');
    await input.fill('rainbow facet');
    await page.waitForTimeout(250);
    const labels = await page.locator('#gsearch-results .gsearch-lab').allTextContents();
    const facetHits = labels.filter((l) => l.includes('Rainbow Facet:'));
    // results cap at 10; assert the facets dominate the result list
    expect(facetHits.length).toBeGreaterThanOrEqual(5);
    // and a specific element query lands its exact card (plain-substring index)
    await input.fill('facet: cold death');
    await page.waitForTimeout(250);
    const top = (await page.locator('#gsearch-results .gsearch-lab').first().textContent()) || '';
    expect(top).toContain('Rainbow Facet: Cold Death');
  });
});
