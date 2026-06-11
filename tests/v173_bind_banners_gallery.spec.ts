import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v173 — the binds best-roll section gains a "top 3 bind targets" picture gallery
// (#binds-top-gallery) and every bind ID card now shows its OWN photo under the
// in-game health-bar: Hephasto carries a real screenshot-verified data-URI banner
// (BIND_SU_BANNER), while Lister / The Smith — who have NO verified screenshot —
// keep ONLY their health-bar replica (zero fabricated image). The gallery shows the
// three S/A binds with their verified hp-bars (Lister, Hephasto) + Hephasto's banner,
// and an honest "1 more to go" placeholder for The Smith. Each card routes to its
// bind ID card via openBindSUByName. Additive: bindSUHpSection / renderAuraBestRoll
// are untouched except for the appended banner + the new gallery render.

async function openBind(page: any, name: string) {
  await page.evaluate((n: string) => (window as any).openBindSUByName(n), name);
  await page.waitForTimeout(250);
}

test.describe('v173 bind ID-card banners + top-3 picture gallery', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(900); // let _v39_whenReady gallery render run
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('binds'));
    await page.waitForTimeout(250);
  });

  test('Hephasto bind ID card renders his real screenshot banner under the hp-bar', async ({ page }) => {
    await openBind(page, 'Hephasto the Armorer');
    const r = await page.evaluate(() => {
      const box = document.getElementById('bindsu-detail')!;
      // Desktop golden-merge: the banner became a 3-slot best-roll gallery; the verified
      // Hephasto screenshot is the single FILLED slot (still a lazy data-URI, never a URL).
      const fig = box.querySelector('.su-hpbar-sec .su-banner-gallery .su-banner-slot.filled img') as HTMLImageElement | null;
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

  test('the top-3 gallery renders all three S/A binds, 2 verified + 1 placeholder', async ({ page }) => {
    const r = await page.evaluate(() => {
      // ensure the best-roll section is expanded so the gallery is in the live DOM
      const cards = [...document.querySelectorAll('#binds-top-gallery .btg-card')] as HTMLElement[];
      return {
        count: cards.length,
        names: cards.map((c) => (c.querySelector('.btg-name')?.textContent || '').trim()),
        withBar: cards.filter((c) => !!c.querySelector('.hpbar')).length,
        todo: cards.filter((c) => c.classList.contains('btg-card-todo')).length,
        hephBanner: cards.some((c) => /Hephasto/.test(c.textContent || '') && !!c.querySelector('.su-banner-gallery .su-banner-slot.filled img')),
      };
    });
    expect(r.count).toBe(3);
    expect(r.names).toEqual(['Lister the Tormentor', 'Hephasto the Armorer', 'The Smith']);
    expect(r.withBar).toBe(2);   // Lister + Hephasto verified hp-bars
    expect(r.todo).toBe(1);      // The Smith — honest "1 more to go" slot
    expect(r.hephBanner).toBe(true);
  });

  test('clicking a gallery card opens that bind ID card', async ({ page }) => {
    await page.evaluate(() => {
      const cards = [...document.querySelectorAll('#binds-top-gallery .btg-card')] as HTMLElement[];
      const heph = cards.find((c) => /Hephasto/.test(c.textContent || ''))!;
      heph.click();
    });
    await page.waitForTimeout(300);
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
      // Desktop golden-merge: BIND_SU_BANNER is now the 3-slot best-roll shape
      // { name: { target, rolls:[{src, label, note}] } } — the verified Hephasto
      // screenshot lives at rolls[0].src (still a data-URI JPEG, never a URL).
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

  test('no console errors across the banner + gallery flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await openBind(page, 'Hephasto the Armorer');
    await openBind(page, 'Lister the Tormentor');
    await page.evaluate(() => (window as any).renderBindTopGallery && (window as any).renderBindTopGallery());
    await page.waitForTimeout(150);
    expect(errors).toEqual([]);
  });
});
