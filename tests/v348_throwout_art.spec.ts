import { test, expect } from '@playwright/test';

// v348 — throw-out (unmatched read) items + Magic & Rare rows in the Registered panel get HD art +
// a hover tooltip, so you can SEE what's being discarded (a real unique vs a junk socketed base).

const URL = 'file://' + process.cwd() + '/bible.html';

test.describe('v348 throw-out art', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('d2r_unknownReads', JSON.stringify([
        'Axe of Fechmar',           // a real unique name → should resolve grail/base art
        'Flail (4os low base)',     // socketed base → strip suffix → base sprite
        'Voulge (2os low base)',    // weapon base → voulge sprite
      ]));
    });
    await page.setViewportSize({ width: 1500, height: 950 });
    await page.goto(URL);
    await page.waitForTimeout(1300);
    await page.evaluate(() => (window as any).switchTab('tools'));
  });

  test('throw-out rows render an art image + data-arttip with the suffix stripped', async ({ page }) => {
    const r = await page.evaluate(() => {
      const rows = Array.from(document.querySelectorAll('#vault-registered [data-unknown-read]'));
      const flail = rows.find((x) => (x.getAttribute('data-unknown-read') || '').startsWith('Flail')) as HTMLElement | undefined;
      const voulge = rows.find((x) => (x.getAttribute('data-unknown-read') || '').startsWith('Voulge')) as HTMLElement | undefined;
      return {
        count: rows.length,
        flailArttip: flail?.getAttribute('data-arttip') || '',
        flailImg: flail?.querySelector('.d2art-wrap img')?.getAttribute('src') || '',
        voulgeImg: voulge?.querySelector('.d2art-wrap img')?.getAttribute('src') || '',
      };
    });
    expect(r.count).toBe(3);
    expect(r.flailArttip).toBe('Flail');          // "(4os low base)" stripped for resolution
    expect(r.flailImg).toContain('flail');         // base sprite resolved
    expect(r.voulgeImg).toContain('voulge');
  });
});
