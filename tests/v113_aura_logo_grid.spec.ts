import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v113 — the Warlock bind-aura logo grid. Lister, Hephasto and (new) The Smith each
// carry a glowing, eye-candy aura grid on their super-unique ID card. Each tile leads
// with the actual in-game Paladin-aura icon (verified diablo2.io skill graphics) so
// Konyo knows exactly "what to look for" over the boss's head. Unified logic: ONE
// AURA_ART map + ONE auraGridHtml renderer feeds all three cards.
//   · Lister  = fixed Meditation lead tile + the 7-aura reroll pool (Fanaticism ⭐).
//   · Hephasto= the 7-aura reroll pool (Fanaticism ⭐), no fixed tile.
//   · The Smith= NEW enriched bind card — fixed-only Holy Fire grid (no reroll) +
//     a Baal-parity drop-pool grid (Tristram TZ mlvl 96 / TC85).
test.describe('v113 aura-logo grid + The Smith bind card', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('AURA_ART map + auraArt/auraGridHtml helpers exist (unified logic)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const m = (window as any).AURA_ART || {};
      return {
        keys: Object.keys(m).sort(),
        allHttps: Object.values(m).every((u: any) => /^https:\/\/i\.imgur\.com\/[A-Za-z0-9]+\.gif$/.test(u)),
        artFn: typeof (window as any).auraArt === 'function',
        gridFn: typeof (window as any).auraGridHtml === 'function',
        poolLen: ((window as any).BIND_AURA_POOL || []).length,
      };
    });
    expect(r.keys).toEqual([
      'Blessed Aim', 'Conviction', 'Fanaticism', 'Holy Fire',
      'Holy Freeze', 'Holy Shock', 'Meditation', 'Might',
    ]);
    expect(r.allHttps).toBe(true);
    expect(r.artFn).toBe(true);
    expect(r.gridFn).toBe(true);
    expect(r.poolLen).toBe(7);
  });

  test('exactly the three fully-sourced targets carry an auraGrid descriptor', async ({ page }) => {
    const r = await page.evaluate(() =>
      (SUPER_UNIQUES as any[]).filter((s) => s.auraGrid).map((s) => s.name).sort());
    expect(r).toEqual(['Hephasto the Armorer', 'Lister the Tormentor', 'The Smith']);
  });

  test('Lister card renders the fixed Meditation tile + the Fanaticism target tile with a real img logo', async ({ page }) => {
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('Lister the Tormentor'));
    await page.waitForTimeout(350);
    const r = await page.evaluate(() => {
      const card = document.querySelector('.su-card-rich');
      const grid = card ? card.querySelector('.aura-grid') : null;
      const tiles = grid ? grid.querySelectorAll('.aura-tile') : [];
      const fixed = grid ? grid.querySelector('.aura-tile.aura-fixed') : null;
      const target = grid ? grid.querySelector('.aura-tile.aura-target') : null;
      const imgs = grid ? grid.querySelectorAll('.aura-logo img.d2art-img') : [];
      const firstImgSrc = imgs.length ? (imgs[0] as HTMLImageElement).getAttribute('src') : '';
      const firstImgLazy = imgs.length ? (imgs[0] as HTMLImageElement).getAttribute('loading') : '';
      return {
        hasGrid: !!grid,
        tileCount: tiles.length,
        fixedTxt: fixed ? (fixed.textContent || '') : '',
        targetTxt: target ? (target.textContent || '') : '',
        imgCount: imgs.length,
        firstImgSrc: firstImgSrc || '',
        firstImgLazy,
      };
    });
    expect(r.hasGrid).toBe(true);
    expect(r.tileCount).toBe(8); // fixed Meditation + 7 pool auras
    expect(r.fixedTxt).toContain('Meditation');
    expect(r.fixedTxt).toContain('FIXED');
    expect(r.targetTxt).toContain('Fanaticism');
    expect(r.targetTxt).toContain('TARGET');
    expect(r.imgCount).toBe(8);
    expect(r.firstImgSrc).toMatch(/^https:\/\/i\.imgur\.com\/[A-Za-z0-9]+\.gif$/);
    expect(r.firstImgLazy).toBe('lazy');
  });

  test('Hephasto card renders the 7-aura pool grid with no fixed tile', async ({ page }) => {
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('Hephasto the Armorer'));
    await page.waitForTimeout(350);
    const r = await page.evaluate(() => {
      const card = document.querySelector('.su-card-rich');
      const grid = card ? card.querySelector('.aura-grid') : null;
      const tiles = grid ? grid.querySelectorAll('.aura-tile') : [];
      const fixed = grid ? grid.querySelector('.aura-tile.aura-fixed') : null;
      const target = grid ? grid.querySelector('.aura-tile.aura-target') : null;
      return { hasGrid: !!grid, tileCount: tiles.length, hasFixed: !!fixed, hasTarget: !!target };
    });
    expect(r.hasGrid).toBe(true);
    expect(r.tileCount).toBe(7);
    expect(r.hasFixed).toBe(false);
    expect(r.hasTarget).toBe(true);
  });

  test('The Smith is now an enriched bind card: fixed-only Holy Fire grid + Baal-parity drop pool', async ({ page }) => {
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('The Smith'));
    await page.waitForTimeout(350);
    const r = await page.evaluate(() => {
      const card = document.querySelector('.su-card-rich');
      const callout = card ? card.querySelector('.su-bind-callout') : null;
      const grid = card ? card.querySelector('.aura-grid') : null;
      const tiles = grid ? grid.querySelectorAll('.aura-tile') : [];
      const target = grid ? grid.querySelector('.aura-tile.aura-target') : null;
      const fixed = grid ? grid.querySelector('.aura-tile.aura-fixed') : null;
      const poolIntro = card ? card.querySelector('.su-pool-intro') : null;
      const hellGrid = card ? card.querySelector('.zd-hell-grid') : null;
      return {
        hasCallout: !!callout,
        calloutTxt: callout ? (callout.textContent || '') : '',
        tileCount: tiles.length,
        hasFixed: !!fixed,
        hasTarget: !!target,
        hasPoolIntro: !!poolIntro,
        poolTxt: poolIntro ? (poolIntro.textContent || '') : '',
        hasHellGrid: !!hellGrid,
      };
    });
    expect(r.hasCallout).toBe(true);
    expect(r.calloutTxt).toContain('Holy Fire');
    expect(r.calloutTxt).toContain('no reroll');
    expect(r.tileCount).toBe(1); // fixed-only, no pool tiles
    expect(r.hasFixed).toBe(true);
    expect(r.hasTarget).toBe(false);
    expect(r.hasPoolIntro).toBe(true);
    expect(r.poolTxt).toContain('Tristram');
    expect(r.hasHellGrid).toBe(true);
  });

  test('a non-bind super-unique (Shenk) shows no aura grid', async ({ page }) => {
    await page.evaluate(() => (window as any).jumpToSuperUniqueByName('Shenk the Overseer'));
    await page.waitForTimeout(300);
    const has = await page.evaluate(() => !!document.querySelector('.su-card-rich .aura-grid'));
    expect(has).toBe(false);
  });

  test('no console errors opening the three enriched aura cards', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
    for (const n of ['Lister the Tormentor', 'Hephasto the Armorer', 'The Smith']) {
      await page.evaluate((nm) => (window as any).jumpToSuperUniqueByName(nm), n);
      await page.waitForTimeout(220);
    }
    expect(errs).toEqual([]);
  });
});
