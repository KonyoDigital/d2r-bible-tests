import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v173 — bind ID-card banners. Hephasto carries a real screenshot-verified data-URI
// banner (BIND_SU_BANNER, 3-slot best-roll gallery rendered by bindSUBannerHtml) at
// the TOP of his bind detail card, while Lister / The Smith — who have NO verified
// screenshot — keep ONLY their health-bar replica (zero fabricated image).
// NOTE (corrected 2026-06-12): #binds-top-gallery / .btg-card / renderBindTopGallery
// are LIVE — v186 ships the stacked top-3 gallery (Lister → Hephasto → Smith) and the
// v186 tests below drive it. The banner ALSO lives in the bind detail card.

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

  test('Lister bind ID card: hp-bar + 3-slot tracker with ZERO fabricated images', async ({ page }) => {
    // v186: Lister carries the 3-slot best-roll tracker (rolls:[]) — the gallery
    // renders 3 honest EMPTY slots. Zero fabrication = zero <img>, not zero gallery.
    await openBind(page, 'Lister the Tormentor');
    const r = await page.evaluate(() => {
      const box = document.getElementById('bindsu-detail')!;
      return {
        hasBar: !!box.querySelector('.hpbar'),
        hasGallery: !!box.querySelector('.su-banner-gallery'),
        emptySlots: box.querySelectorAll('.su-banner-gallery .su-banner-slot.empty').length,
        imgs: box.querySelectorAll('.su-banner-gallery img').length,
      };
    });
    expect(r.hasBar).toBe(true);    // his verified health-bar replica IS his picture
    expect(r.hasGallery).toBe(true);
    expect(r.emptySlots).toBe(3);   // 3 slots waiting for real screenshots
    expect(r.imgs).toBe(0);         // zero fabrication — no invented screenshot
  });

  test('the tier-list grid shows the S/A bind targets with their art', async ({ page }) => {
    // The bind tier-list colossal-grid (always visible in the binds tab,
    // alongside the v186 top-gallery) shows the S/A targets
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

  test('BIND_SU_BANNER: Hephasto 1/3 filled (data-URI); Lister/Smith mapped with 3 HONEST empty slots', async ({ page }) => {
    // v186: all three S/A binds carry the 3-slot best-roll tracker. Only Hephasto
    // has a verified screenshot (rolls[0], data-URI). Lister/Smith have rolls:[] —
    // empty slots are honest, fabricated images are not.
    const r = await page.evaluate(() => {
      const m = (window as any).BIND_SU_BANNER || {};
      const heph = m['Hephasto the Armorer'];
      const src = heph && Array.isArray(heph.rolls) && heph.rolls[0] ? heph.rolls[0].src : '';
      return {
        keys: Object.keys(m).sort(),
        hephIsJpeg: typeof src === 'string' && src.startsWith('data:image/jpeg;base64,'),
        hephRolls: heph ? heph.rolls.length : -1,
        hephTarget: heph ? heph.target : -1,
        listerRolls: m['Lister the Tormentor'] ? m['Lister the Tormentor'].rolls.length : -1,
        listerTarget: m['Lister the Tormentor'] ? m['Lister the Tormentor'].target : -1,
        smithRolls: m['The Smith'] ? m['The Smith'].rolls.length : -1,
      };
    });
    expect(r.keys).toEqual(['Hephasto the Armorer', 'Lister the Tormentor', 'The Smith']);
    expect(r.hephIsJpeg).toBe(true);
    expect(r.hephRolls).toBe(3);  // v233: Konyo's phys-immune Fanaticism+Cursed roll → #1; the 2 fire rolls → #2/#3 (all 3 slots filled)
    expect(r.hephTarget).toBe(3);
    expect(r.listerRolls).toBe(0);   // mapped, zero images
    expect(r.listerTarget).toBe(3);  // 3 slots waiting
    expect(r.smithRolls).toBe(0);
  });

  test('v186: the stacked top-3 gallery renders at the best-roll spot — Lister, under it Hephasto, then Smith', async ({ page }) => {
    const r = await page.evaluate(() => {
      const el = document.getElementById('binds-top-gallery')!;
      const cards = [...el.querySelectorAll('.btg-card')] as HTMLElement[];
      const grid = el.querySelector('.btg-grid') as HTMLElement;
      return {
        names: cards.map((c) => (c.querySelector('.btg-name')?.textContent || '').trim()),
        cols: getComputedStyle(grid).gridTemplateColumns.split(' ').length,
        listerHasBar: !!cards[0]?.querySelector('.hpbar'),
        listerKeepsAnatomyCap: /exactly what Lister/.test(cards[0]?.innerHTML || ''),
        listerNoImg: !cards[0]?.querySelector('.su-banner-slot img'),
        hephFilledShot: !!cards[1]?.querySelector('.su-banner-slot.filled img'),
        smithTodo: !!cards[2]?.classList.contains('btg-card-todo'),
      };
    });
    expect(r.names).toEqual(['Lister the Tormentor', 'Hephasto the Armorer', 'The Smith']);
    expect(r.cols).toBe(1); // stacked — "lister image and under it hephasto"
    expect(r.listerHasBar).toBe(true);
    expect(r.listerKeepsAnatomyCap).toBe(true); // the 9-lines anatomy lesson survives
    expect(r.listerNoImg).toBe(true);           // zero fabricated images
    expect(r.hephFilledShot).toBe(true);
    expect(r.smithTodo).toBe(true);
  });

  test('v186: clicking a gallery card opens that bind ID card', async ({ page }) => {
    await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#binds-top-gallery .btg-card')] as HTMLElement[];
      cards.find((c) => /Hephasto/.test(c.textContent || ''))!.click();
    });
    await page.waitForTimeout(300);
    const r = await page.evaluate(() => {
      const box = document.getElementById('bindsu-detail')!;
      return { open: !box.hasAttribute('hidden'), text: box.textContent || '' };
    });
    expect(r.open).toBe(true);
    expect(r.text).toMatch(/Hephasto/);
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
