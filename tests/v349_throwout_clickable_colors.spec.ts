import { test, expect } from '@playwright/test';

// v349 — throw-out items are clickable + show a rich description tooltip on the TEXT (not just the
// image); intake report + journal breakdown item names render in their in-game rarity colour with
// the #arttip hover, matching the rest of the app.

const URL = 'file://' + process.cwd() + '/bible.html';

test.describe('v349 throw-out clickable + rarity colours', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem('d2r_unknownReads', JSON.stringify(['Axe of Fechmar', 'Broad Sword (4os low base)']));
    });
    await page.setViewportSize({ width: 1500, height: 950 });
    await page.goto(URL);
    await page.waitForTimeout(1300);
    await page.evaluate(() => (window as any).switchTab('tools'));
  });

  test('_arttipResolve gives a throw-out item a rich description + base art (text hover, not just image)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const vr = (window as any)._arttipResolve('Broad Sword (4os low base)');
      return { rich: vr.rich, hasArt: !!vr.artSrc, desc: vr.desc || '' };
    });
    expect(r.rich).toBe(true);
    expect(r.hasArt).toBe(true);
    expect(r.desc).toContain('Throw-out');
    expect(r.desc).toContain('4 sockets');
  });

  test('throw-out rows are clickable (openDrop) and hover the FULL name', async ({ page }) => {
    const r = await page.evaluate(() => {
      const rows = Array.from(document.querySelectorAll('#vault-registered [data-unknown-read]'));
      const bs = rows.find((x) => (x.getAttribute('data-unknown-read') || '').startsWith('Broad Sword')) as HTMLElement | undefined;
      return {
        onclick: bs?.getAttribute('onclick') || '',
        arttip: bs?.getAttribute('data-arttip') || '',
      };
    });
    expect(r.onclick).toContain('openDrop');
    expect(r.arttip).toBe('Broad Sword (4os low base)');   // full name → resolves the rich throw-out card
  });

  test('clicking a throw-out item opens its review card', async ({ page }) => {
    await page.evaluate(() => (window as any).openDrop('Broad Sword (4os low base)'));
    const r = await page.evaluate(() => {
      const card = document.querySelector('#item-detail .magicfind-card');
      return { shown: !!card, text: card?.textContent || '' };
    });
    expect(r.shown).toBe(true);
    expect(r.text).toContain('Throw-out');
  });

  test('_vColorName renders a name in its rarity colour with a data-arttip hover', async ({ page }) => {
    const r = await page.evaluate(() => {
      const html = (window as any)._vColorName('Windforce');
      const d = document.createElement('div'); d.innerHTML = html;
      const span = d.firstElementChild as HTMLElement;
      return { color: span?.getAttribute('style') || '', arttip: span?.getAttribute('data-arttip') || '' };
    });
    expect(r.color).toContain('color');           // rarity colour applied
    expect(r.arttip).toBe('Windforce');           // hover hook present
  });
});
