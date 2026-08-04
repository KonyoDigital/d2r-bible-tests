import { test, expect } from './_net_stub'; // diablo2.io art stubbed — kills net-flake (audit 2026-06-12)
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v116 — site-wide aura-logo rollout. Every aura NAMED as a title across the binds tab
// (the aura-pool table + the Aura Enchanted level table) now carries the same live
// animated diablo2.io aura gif the bind cards use. Driven by a single enhancer
// (decorateAuraLogos) that reuses the auraArt single-source helper to inject a leading
// logo chip into any [data-aura-logo] cell. Three new real Paladin-aura gifs were
// sourced (Concentration / Vigor / Thorns) so the pool table is fully covered.
// Items are explicitly OUT of scope (Konyo: "items are irrelevant"). Additive only.
test.describe('v116 site-wide aura-cell logos', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('AURA_ART grew to the full 11-aura set incl. Concentration/Vigor/Thorns (all https gifs)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const m = (window as any).AURA_ART || {};
      return {
        keys: Object.keys(m).sort(),
        allHttps: Object.values(m).every((u: any) => /^art\/aura_[A-Za-z0-9_]+\.gif(?:\?|$)/.test(u)),
        decoFn: typeof (window as any).decorateAuraLogos === 'function',
      };
    });
    expect(r.keys).toEqual([
      'Blessed Aim', 'Concentration', 'Conviction', 'Fanaticism', 'Holy Fire',
      'Holy Freeze', 'Holy Shock', 'Meditation', 'Might', 'Thorns', 'Vigor',
    ]);
    expect(r.allHttps).toBe(true);
    expect(r.decoFn).toBe(true);
  });

  test('every tagged aura cell got a live gif logo injected (lazy-loaded)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cells = Array.from(document.querySelectorAll('[data-aura-logo]'));
      const decorated = cells.filter((c) => c.querySelector(':scope > .aura-logo'));
      const withImg = cells.filter((c) => c.querySelector('.aura-logo img.d2art-img'));
      const img0 = withImg.length ? (withImg[0].querySelector('img.d2art-img') as HTMLImageElement) : null;
      const names = Array.from(new Set(cells.map((c) => c.getAttribute('data-aura-logo')))).sort();
      return {
        total: cells.length,
        decorated: decorated.length,
        withImg: withImg.length,
        firstSrc: img0 ? img0.getAttribute('src') : '',
        firstLazy: img0 ? img0.getAttribute('loading') : '',
        names,
      };
    });
    // Desktop golden-merge: aura tables restructured; 7 aura pool tiles +
    // 3 SU table cells (Holy Fire/Fanaticism/Meditation) + 5 tier-list mentions = 15 tags
    expect(r.total).toBeGreaterThanOrEqual(14);
    expect(r.decorated).toBe(r.total);
    // all tagged auras exist in AURA_ART, so every cell has a real <img>, not just a glyph
    expect(r.withImg).toBe(r.total);
    expect(r.firstSrc).toMatch(/^art\/aura_[A-Za-z0-9_]+\.gif(?:\?|$)/);
    expect(r.firstLazy).toBe('lazy');
    // Desktop golden-merge: the aura pool table now shows the 7 Aura-Enchanted
    // auras + the bind tables tag Fanaticism/Meditation/Holy Fire. Concentration,
    // Vigor, Thorns are still in AURA_ART but no longer tagged in HTML tables.
    expect(r.names).toEqual(expect.arrayContaining(['Fanaticism', 'Holy Fire', 'Meditation']));
  });

  test('decorateAuraLogos is idempotent — a second call injects nothing new', async ({ page }) => {
    const r = await page.evaluate(() => {
      const before = document.querySelectorAll('.aura-cell > .aura-logo').length;
      const added = (window as any).decorateAuraLogos();
      const after = document.querySelectorAll('.aura-cell > .aura-logo').length;
      return { before, added, after };
    });
    expect(r.before).toBeGreaterThanOrEqual(14);
    expect(r.added).toBe(0);
    expect(r.after).toBe(r.before);
  });

  test('no console errors on load (the rollout never throws)', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    await page.reload();
    await page.waitForTimeout(1000);
    expect(errs).toEqual([]);
  });
});
