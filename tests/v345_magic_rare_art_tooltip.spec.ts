import { test, expect } from '@playwright/test';

// v345 — Magic & Rare keepers (rolled-name rares) get HD base art + the same image+description
// floating tooltip the grail/Socketed items have. Rolled items have no fixed stat block, so the
// card is the keeper format (quality · base · roll-type · blurb), matching the Socketed/EXTRA tip.

const URL = 'file://' + process.cwd() + '/bible.html';

test.describe('v345 magic & rare art + tooltip', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('d2r_magicFinds', JSON.stringify({
        "Blackbog's Sharp Cinquedeas": { q: 'rare', base: 'Cinquedeas' },
        'Steelgoad Voulge': { q: 'rare', base: 'Voulge' },
        "M'avina's Catcher": { q: 'rare', base: 'Grand Matron Bow' },
      }));
    });
    await page.setViewportSize({ width: 1500, height: 950 });
    await page.goto(URL);
    await page.waitForTimeout(1300);
    await page.evaluate(() => (window as any).switchTab('tools'));
  });

  test('_magicArtSrc resolves weapon-class bases to a self-hosted sprite (no ◆ glyph)', async ({ page }) => {
    const r = await page.evaluate(() => ({
      cinq: (window as any)._magicArtSrc ? (window as any)._magicArtSrc('Cinquedeas') : undefined,
      voulge: (window as any)._magicArtSrc ? (window as any)._magicArtSrc('Voulge') : undefined,
      bow: (window as any)._magicArtSrc ? (window as any)._magicArtSrc('Grand Matron Bow') : undefined,
    }));
    expect(r.cinq).toMatch(/sword/i);
    expect(r.voulge).toContain('voulge');
    expect(r.bow).toContain('bow');
  });

  test('_arttipResolve returns a rich keeper card + base-art src for a rolled rare', async ({ page }) => {
    const r = await page.evaluate(() => {
      const vr = (window as any)._arttipResolve("Blackbog's Sharp Cinquedeas");
      return { rich: vr.rich, hasArt: !!vr.artSrc, art: vr.artSrc || '', desc: vr.desc || '' };
    });
    expect(r.rich).toBe(true);
    expect(r.hasArt).toBe(true);
    expect(r.art).toMatch(/sword/i);
    expect(r.desc).toContain('Magic &amp; Rare keeper');
    expect(r.desc).toContain('Rare');     // quality label
    expect(r.desc).toContain('Cinquedeas'); // base type
  });

  test('rendered magic-find cell carries data-arttip so hover fires the rich card', async ({ page }) => {
    const r = await page.evaluate(() => {
      const cells = Array.from(document.querySelectorAll('.vmc-magicfind'));
      const cell = cells.find((c) => (c.getAttribute('data-magic-find') || '').includes('Voulge')) as HTMLElement | undefined;
      return {
        count: cells.length,
        cellArttip: cell?.getAttribute('data-arttip') || '',
        nameArttip: cell?.querySelector('.vm-cell-name')?.getAttribute('data-arttip') || '',
        hasImg: !!cell?.querySelector('.d2art-wrap img'),
      };
    });
    expect(r.count).toBeGreaterThanOrEqual(3);
    expect(r.cellArttip).toContain('Voulge');
    expect(r.nameArttip).toContain('Voulge');
    expect(r.hasImg).toBe(true);   // weapon base now resolves to a sprite, so the cell shows art
  });
});
