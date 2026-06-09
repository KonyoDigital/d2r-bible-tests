import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v73 — verified diablo2.io AREA artwork on every terror-zone card. Each TZ_ZONES entry
// maps (by name) to its primary area's scene graphic. v148: the big top banner was retired;
// the SAME verified art now renders in a small boss-header-style emblem (.tz-zone-emblem) at
// the head of the title row. Every slug was HEAD-probed live (HTTP 200 + image content-type)
// before shipping, and a hard onerror keeps a 404 from ever showing a broken-image box.
test.describe('v73 TZ zone artwork emblems', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="tz"]');
    await page.waitForTimeout(250);
  });

  test('TZ_ZONE_ART is a global map of verified act-area slugs', async ({ page }) => {
    const r = await page.evaluate(() => {
      const m = (window as any).TZ_ZONE_ART;
      const vals = m ? Object.values(m) as string[] : [];
      return {
        type: typeof m,
        len: vals.length,
        allActSlugs: vals.every((s) => /^act\d-[a-z0-9]+$/.test(s)),
        arcane: m?.['Arcane Sanctuary'],
        catacombs: m?.['Catacombs L4'],
      };
    });
    expect(r.type).toBe('object');
    expect(r.len).toBe(11);
    expect(r.allActSlugs).toBe(true);
    expect(r.arcane).toBe('act2-arcanesanctuary');
    expect(r.catacombs).toBe('act1-catacombs');
  });

  test('every TZ zone card renders a verified area banner (lazy + onerror fallback)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#tz-zones-container .tz-zone-card')];
      const banners = cards.map((c) => c.querySelector('.tz-zone-emblem .d2art-img') as HTMLImageElement | null);
      const withArt = banners.filter(Boolean) as HTMLImageElement[];
      return {
        cardCount: cards.length,
        bannerCount: withArt.length,
        allDiablo2io: withArt.every((i) => /^https:\/\/diablo2\.io\/styles\/zulu\/theme\/images\/items\/act\d-[a-z0-9]+_graphic\.png$/.test(i.getAttribute('src') || '')),
        allLazy: withArt.every((i) => i.getAttribute('loading') === 'lazy'),
        allOnerror: withArt.every((i) => (i.getAttribute('onerror') || '').includes('d2art-failed')),
      };
    });
    expect(r.cardCount).toBeGreaterThanOrEqual(11);
    expect(r.bannerCount).toBe(11);           // all 11 TZ_ZONES carry verified art
    expect(r.allDiablo2io).toBe(true);
    expect(r.allLazy).toBe(true);
    expect(r.allOnerror).toBe(true);
  });

  test('a known zone shows its exact area graphic (Arcane Sanctuary)', async ({ page }) => {
    const src = await page.evaluate(() => {
      const card = [...document.querySelectorAll('#tz-zones-container .tz-zone-card')]
        .find((c) => /Arcane Sanctuary/.test(c.querySelector('.tz-zone-name')?.textContent || ''));
      return (card?.querySelector('.tz-zone-emblem .d2art-img') as HTMLImageElement)?.getAttribute('src') || '';
    });
    expect(src).toMatch(/act2-arcanesanctuary_graphic\.png$/);
  });

  test('the permanent lvl-85 cross-link card (The Pit) also gets its scene banner', async ({ page }) => {
    const src = await page.evaluate(() => {
      const card = document.querySelector('#tz-zones-container .tz-crosslink-card');
      return (card?.querySelector('.tz-zone-emblem .d2art-img') as HTMLImageElement)?.getAttribute('src') || '';
    });
    expect(src).toMatch(/act1-underground_graphic\.png$/);
  });

  test('no console errors rendering the TZ tab with banners', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.click('.tab[data-tab="tz"]');
    await page.waitForTimeout(250);
    expect(errors).toEqual([]);
  });
});
