// v193 — fullscreen HD lightbox for the bind-roll screenshots.
// Clicking a filled .su-banner-slot screenshot (top gallery OR bind detail card)
// opens #gild-lightbox fullscreen with that image + its figcaption. The listener
// runs at CAPTURE phase so it beats the .btg-card inline onclick routing — a
// screenshot click means "view HD", never "route to the bind card".
import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v193 screenshot lightbox', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2200);
    await page.evaluate(() => (window as any).switchTab('binds'));
    await page.waitForTimeout(800);
  });

  test('clicking a gallery screenshot opens the lightbox with that image, WITHOUT routing', async ({ page }) => {
    const r = await page.evaluate(() => {
      const img = document.querySelector('#binds-top-gallery .su-banner-slot.filled img') as HTMLImageElement;
      if (!img) return { img: false };
      const detailHiddenBefore = (document.getElementById('bindsu-detail') as HTMLElement)?.hidden;
      img.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
      const lb = document.getElementById('gild-lightbox');
      return {
        img: true,
        cursor: getComputedStyle(img).cursor,
        open: lb?.classList.contains('show') || false,
        srcMatch: (lb?.querySelector('.glb-img') as HTMLImageElement)?.src === img.src,
        hasCaption: ((lb?.querySelector('.glb-cap')?.textContent || '').length > 10),
        scrollLocked: document.documentElement.classList.contains('glb-lock'),
        // capture-phase block: the parent .btg-card onclick (openBindSUByName) must NOT fire
        routed: (document.getElementById('bindsu-detail') as HTMLElement)?.hidden !== detailHiddenBefore,
      };
    });
    expect(r.img).toBe(true);
    // v605 — the app-wide Konyonized gauntlet (one D2 hand for EVERYTHING, !important) correctly
    // overrides the old zoom-in affordance; the thumb is still clickable — that's what the rest of
    // this test proves. Accept either the gauntlet data-URI or a bare zoom-in (pre-v605 engines).
    expect(r.cursor).toMatch(/data:image\/png|zoom-in/);
    expect(r.open).toBe(true);
    expect(r.srcMatch).toBe(true);
    expect(r.hasCaption).toBe(true);
    expect(r.scrollLocked).toBe(true);
    expect(r.routed).toBe(false);
  });

  test('Escape closes and unlocks scroll; click-anywhere closes too', async ({ page }) => {
    await page.evaluate(() => {
      const img = document.querySelector('#binds-top-gallery .su-banner-slot.filled img') as HTMLImageElement;
      img.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
    });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(150);
    const r1 = await page.evaluate(() => ({
      closed: !document.getElementById('gild-lightbox')?.classList.contains('show'),
      unlocked: !document.documentElement.classList.contains('glb-lock'),
    }));
    expect(r1.closed).toBe(true);
    expect(r1.unlocked).toBe(true);
    // click-to-close path
    const r2 = await page.evaluate(() => {
      const img = document.querySelector('#binds-top-gallery .su-banner-slot.filled img') as HTMLImageElement;
      img.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
      const lb = document.getElementById('gild-lightbox') as HTMLElement;
      const opened = lb.classList.contains('show');
      lb.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      return { opened, closed: !lb.classList.contains('show') };
    });
    expect(r2.opened).toBe(true);
    expect(r2.closed).toBe(true);
  });

  test('lightbox also fires from the bind detail card gallery (bindSUBannerHtml)', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any).openBindSUByName('Hephasto the Armorer');
      const img = document.querySelector('#bindsu-detail .su-banner-slot.filled img') as HTMLImageElement;
      if (!img) return { img: false };
      img.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
      const lb = document.getElementById('gild-lightbox');
      return { img: true, open: lb?.classList.contains('show') || false };
    });
    expect(r.img).toBe(true);
    expect(r.open).toBe(true);
  });

  test('empty slots and non-gallery images do NOT trigger the lightbox', async ({ page }) => {
    const r = await page.evaluate(() => {
      (window as any)._gildLightboxClose && (window as any)._gildLightboxClose();
      const empty = document.querySelector('#binds-top-gallery .su-banner-slot.empty') as HTMLElement;
      if (empty) empty.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
      const after1 = document.getElementById('gild-lightbox')?.classList.contains('show') || false;
      const anyArt = document.querySelector('.d2art-img') as HTMLElement;
      if (anyArt) anyArt.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
      const after2 = document.getElementById('gild-lightbox')?.classList.contains('show') || false;
      return { after1, after2 };
    });
    expect(r.after1).toBe(false);
    expect(r.after2).toBe(false);
  });

  test('no console errors through an open/close cycle', async ({ page }) => {
    const errs: string[] = [];
    page.on('pageerror', e => errs.push(e.message));
    page.on('console', m => {
      if (m.type() === 'error' && !/net::|Failed to load resource/.test(m.text())) errs.push(m.text());
    });
    await page.evaluate(() => {
      const img = document.querySelector('#binds-top-gallery .su-banner-slot.filled img') as HTMLImageElement;
      img.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
    });
    await page.waitForTimeout(400);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
    expect(errs).toEqual([]);
  });
});
