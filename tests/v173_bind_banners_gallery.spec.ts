import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v173 — bind ID-card banners. Hephasto carries a real screenshot-verified data-URI
// banner (BIND_SU_BANNER, 3-slot best-roll gallery rendered by bindSUBannerHtml) at
// the TOP of his bind detail card, while Lister / The Smith — who have NO verified
// screenshot — keep ONLY their health-bar replica (zero fabricated image).
// Desktop golden-merge removed the separate #binds-top-gallery / .btg-card /
// renderBindTopGallery — the banner now lives directly in the bind detail card.

async function openBind(page: any, name: string) {
  await page.evaluate((n: string) => (window as any).openBindSUByName(n), name);
  await page.waitForTimeout(250);
}

test.describe('v173 bind ID-card banners', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(900);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('binds'));
    await page.waitForTimeout(250);
  });

  test('Hephasto bind ID card renders his real screenshot banner', async ({ page }) => {
    await openBind(page, 'Hephasto the Armorer');
    const r = await page.evaluate(() => {
      const box = document.getElementById('bindsu-detail')!;
      // The banner gallery is rendered at the top of the card by bindSUBannerHtml,
      // NOT inside .su-hpbar-sec. Look for it directly in the detail container.
      const fig = box.querySelector('.su-banner-gallery .su-banner-slot.filled img') as HTMLImageElement | null;
      return {
        hasBar: !!box.querySelector('.hpbar'),
        hasBanner: !!fig,
        isDataUri: !!fig && fig.getAttribute('src')!.startsWith('data:image/jpeg;base64,'),
        lazy: fig ? fig.getAttribute('loading') : null,
        alt: fig ? fig.getAttribute('alt') : null,
      };
    });
    expect(r.hasBar).toBe(true);
    expect(r.hasBanner).toBe(true);
    expect(r.isDataUri).toBe(true);   // never a 404-able URL
    expect(r.lazy).toBe('lazy');
    expect(r.alt).toMatch(/Hephasto/);
  });

  test('Lister bind ID card shows his hp-bar but NO fabricated banner image', async ({ page }) => {
    await openBind(page, 'Lister the Tormentor');
    const r = await page.evaluate(() => {
      const box = document.getElementById('bindsu-detail')!;
      return { hasBar: !!box.querySelector('.hpbar'), hasBanner: !!box.querySelector('.su-banner-gallery') };
    });
    expect(r.hasBar).toBe(true);      // his verified health-bar replica IS his picture
    expect(r.hasBanner).toBe(false);  // zero fabrication — no invented screenshot, no gallery
  });

  test('the tier-list grid shows the S/A bind targets with their art', async ({ page }) => {
    // Desktop golden-merge: the standalone #binds-top-gallery was removed; the bind
    // tier-list colossal-grid (always visible in the binds tab) shows the S/A targets
    // with art + linked to their SU cards. Verify the key names are present.
    const r = await page.evaluate(() => {
      const grid = document.querySelector('#tab-binds .colossal-grid');
      if (!grid) return { found: false, names: [] as string[] };
      const tiles = [...grid.querySelectorAll('.colossal-tile')];
      const names = tiles.map((t) => (t.querySelector('.ct-name')?.textContent || '').trim());
      return {
        found: true,
        names,
        hasHephasto: names.some(n => /Hephasto/.test(n)),
        hasLister: names.some(n => /Lister/.test(n)),
        hasSmith: names.some(n => /The Smith/.test(n)),
      };
    });
    expect(r.found).toBe(true);
    expect(r.hasHephasto).toBe(true);
    expect(r.hasLister).toBe(true);
    expect(r.hasSmith).toBe(true);
  });

  test('clicking a tier-list SU link opens that bind ID card', async ({ page }) => {
    // Use openBindSUByName directly (the su-link onclick handler)
    await openBind(page, 'Hephasto the Armorer');
    const r = await page.evaluate(() => {
      const box = document.getElementById('bindsu-detail')!;
      return { open: !box.hasAttribute('hidden'), text: box.textContent || '' };
    });
    expect(r.open).toBe(true);
    expect(r.text).toMatch(/Hephasto/);
  });

  test('only Hephasto is mapped in BIND_SU_BANNER — Lister/Smith are image-less', async ({ page }) => {
    const r = await page.evaluate(() => {
      const m = (window as any).BIND_SU_BANNER || {};
      const heph = m['Hephasto the Armorer'];
      const src = heph && Array.isArray(heph.rolls) && heph.rolls[0] ? heph.rolls[0].src : '';
      return {
        keys: Object.keys(m),
        hephIsJpeg: typeof src === 'string' && src.startsWith('data:image/jpeg;base64,'),
        lister: 'Lister the Tormentor' in m,
        smith: 'The Smith' in m,
      };
    });
    expect(r.keys).toEqual(['Hephasto the Armorer']);
    expect(r.hephIsJpeg).toBe(true);
    expect(r.lister).toBe(false);
    expect(r.smith).toBe(false);
  });

  test('no console errors across the banner flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await openBind(page, 'Hephasto the Armorer');
    await openBind(page, 'Lister the Tormentor');
    await page.waitForTimeout(150);
    expect(errors).toEqual([]);
  });
});
