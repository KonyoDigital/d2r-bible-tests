import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v146 — Reference-tab title unification. The last two flat `.golden-underline`
// headers ("Tips & Wisdom" + "Methodology") now render in the SAME boss-header
// style as every other Reference section: a boxed `.sec-h-art` emblem + a glowing
// `.sec-h-t` serif title + a `.sec-chev` chevron, collapsible via toggleSec. The
// whole tab now reads as one uniform stack of editorial section headers.
test.describe('v146 reference tab header unification', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('ref'));
    await page.waitForTimeout(300);
  });

  test('no flat golden-underline headers remain in the reference extras', async ({ page }) => {
    const gone = await page.evaluate(() =>
      !document.querySelector('.v40-extras .golden-underline'));
    expect(gone).toBe(true);
  });

  test('Tips & Wisdom + Methodology are structured collapsible boss-style headers', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ext = document.querySelector('.v40-extras');
      const hs = [...(ext?.querySelectorAll('.sec-h') || [])];
      return {
        count: hs.length,
        titles: hs.map((h) => h.querySelector('.sec-h-t')?.textContent?.trim() || ''),
        allStructured: hs.every((h) => !!h.querySelector('.sec-h-art') && !!h.querySelector('.sec-h-t') && !!h.querySelector('.sec-chev')),
        allCollapsible: hs.every((h) => (h.getAttribute('onclick') || '').includes('toggleSec(this)')),
        allStartCollapsed: hs.every((h) => h.classList.contains('collapsed')),
        bodiesHidden: hs.every((h) => !!(h.nextElementSibling as HTMLElement)?.hasAttribute('hidden')),
      };
    });
    expect(r.count).toBe(2);
    expect(r.titles).toEqual(['Tips & Wisdom', 'Methodology']);
    expect(r.allStructured).toBe(true);
    expect(r.allCollapsible).toBe(true);
    expect(r.allStartCollapsed).toBe(true);
    expect(r.bodiesHidden).toBe(true);
  });

  test('clicking Tips & Wisdom expands its bento body', async ({ page }) => {
    await page.evaluate(() => {
      const h = [...document.querySelectorAll('.v40-extras .sec-h')]
        .find((x) => /Tips/.test(x.textContent || '')) as HTMLElement | undefined;
      h?.click();
    });
    await page.waitForTimeout(200);
    const r = await page.evaluate(() => {
      const h = [...document.querySelectorAll('.v40-extras .sec-h')]
        .find((x) => /Tips/.test(x.textContent || '')) as HTMLElement | undefined;
      const body = h?.nextElementSibling as HTMLElement | null;
      return {
        notCollapsed: !h?.classList.contains('collapsed'),
        bodyVisible: !!body && !body.hasAttribute('hidden'),
        hasBento: !!body?.querySelector('.tips-bento'),
      };
    });
    expect(r.notCollapsed).toBe(true);
    expect(r.bodyVisible).toBe(true);
    expect(r.hasBento).toBe(true);
  });

  test('no console errors rendering the unified reference tab', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1000);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('ref'));
    await page.waitForTimeout(300);
    expect(errors).toEqual([]);
  });
});
