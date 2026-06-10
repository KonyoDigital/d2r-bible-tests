import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v170 — Lister the Tormentor / Hephasto the Armorer / The Smith become art-chipped,
// clickable, routable keywords (data-su-route) across the Reference + TZ tabs and the
// boss-card field manuals. A delegated capture-phase router (closest of
// [data-art-route],[data-boss-route],[data-su-route]) sends a data-su-route click to
// window.openBindSUByName(name), which now SURFACES the binds tab first (the v170 fix —
// it used to render into the hidden #bindsu-detail and land silently on a cross-tab
// route). This spec regression-locks both v170 bug fixes:
//   (a) the router's closest() selector must include [data-su-route] (SU-only spans
//       previously bailed early because the selector only matched art/boss routes), and
//   (b) openBindSUByName must switchTab('binds') + force-open the card when arriving
//       from another tab.
// Plus: the 3 names are enriched (data-su-route) and art-decorated (.d2art-wrap via the
// data-art-logo logo injector). Additive UI — every existing .su-link onclick route on
// the binds tab is untouched.
const SU_NAMES = ['Lister the Tormentor', 'Hephasto the Armorer', 'The Smith'];

// fire a bubbling click on a node (the static ref-tab spans live inside a COLLAPSED
// .sec-body[hidden], so a physical Playwright .click() can't reach them — but the
// document-level capture router still catches a dispatched bubbling click).
async function routeClick(page: any, selector: string) {
  await page.evaluate((sel: string) => {
    const el = document.querySelector(sel) as HTMLElement;
    if (!el) throw new Error('no node for ' + sel);
    el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
  }, selector);
  await page.waitForTimeout(300);
}

async function bindCardState(page: any) {
  return await page.evaluate(() => {
    const box = document.getElementById('bindsu-detail');
    const tab = document.querySelector('.tabs .tab.active') as HTMLElement | null;
    return {
      activeTab: tab ? tab.dataset.tab : null,
      open: !!box && !box.hasAttribute('hidden'),
      dataOpen: box ? box.getAttribute('data-open') : null,
      text: box ? (box.textContent || '') : '',
    };
  });
}

test.describe('v170 super-unique keyword routing (data-su-route)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(900); // let _v39_whenReady decorators (logos) run
  });

  test('the 3 v170 names are enriched as data-su-route spans and art-decorated at load', async ({ page }) => {
    const r = await page.evaluate((names: string[]) => {
      const all = Array.from(document.querySelectorAll('[data-su-route]')) as HTMLElement[];
      const perName: Record<string, number> = {};
      names.forEach((n) => { perName[n] = 0; });
      let decorated = 0;
      all.forEach((el) => {
        const n = el.getAttribute('data-su-route') || '';
        if (n in perName) perName[n]++;
        if (el.querySelector('.d2art-wrap')) decorated++;
      });
      return { total: all.length, perName, decorated };
    }, SU_NAMES);
    // 9 static spans in the DOM at load (ref + tz); boss-card spans render on open
    expect(r.total).toBeGreaterThanOrEqual(9);
    for (const n of SU_NAMES) expect(r.perName[n]).toBeGreaterThanOrEqual(1);
    // every enriched span carries its injected diablo2.io art chip
    expect(r.decorated).toBe(r.total);
  });

  test('the delegated router matches data-su-route — a cross-tab click opens the bind card', async ({ page }) => {
    // start NOT on the binds tab so the cross-tab path is exercised
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('ref'));
    await page.waitForTimeout(150);
    await routeClick(page, '[data-su-route="Hephasto the Armorer"]');
    const s = await bindCardState(page);
    expect(s.activeTab).toBe('binds');     // router → openBindSUByName → switchTab('binds')
    expect(s.open).toBe(true);             // card surfaced (not stuck in hidden panel)
    expect(s.dataOpen).not.toBeNull();
    expect(s.text).toMatch(/Hephasto/);
  });

  test('openBindSUByName resolves all three names and surfaces each card', async ({ page }) => {
    for (const name of SU_NAMES) {
      // bounce off the binds tab each iteration to re-exercise the cross-tab surface
      await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
      await page.waitForTimeout(120);
      await page.evaluate((n: string) => (window as any).openBindSUByName(n), name);
      await page.waitForTimeout(250);
      const s = await bindCardState(page);
      expect(s.activeTab).toBe('binds');
      expect(s.open).toBe(true);
      // a distinctive fragment of each name renders in the card
      const frag = name.split(' ')[name.split(' ').length - 1]; // Tormentor / Armorer / Smith
      expect(s.text).toContain(frag);
    }
  });

  test('a cross-tab route force-OPENS (never toggles closed) on repeated arrival', async ({ page }) => {
    // open The Smith from the TZ tab
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
    await page.waitForTimeout(120);
    await page.evaluate(() => (window as any).openBindSUByName('The Smith'));
    await page.waitForTimeout(250);
    expect((await bindCardState(page)).open).toBe(true);
    // leave binds, route to the SAME name again — must re-open, not toggle shut
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('tz'));
    await page.waitForTimeout(120);
    await page.evaluate(() => (window as any).openBindSUByName('The Smith'));
    await page.waitForTimeout(250);
    const s = await bindCardState(page);
    expect(s.activeTab).toBe('binds');
    expect(s.open).toBe(true);
    expect(s.text).toMatch(/Smith/);
  });

  test("Baal's field manual renders a routable Lister keyword (boss-card data string)", async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('bosses'));
    await page.waitForTimeout(200);
    await page.evaluate(() => (window as any).openBossDetail && (window as any).openBossDetail('baal'));
    await page.waitForTimeout(450); // boss card + field-manual inject + decorateItemLogos (60ms)
    const r = await page.evaluate(() => {
      const panel = document.getElementById('boss-detail-panel');
      const span = panel ? panel.querySelector('[data-su-route="Lister the Tormentor"]') : null;
      return {
        present: !!span,
        decorated: !!(span && span.querySelector('.d2art-wrap')),
      };
    });
    expect(r.present).toBe(true);
    expect(r.decorated).toBe(true);
    // clicking the boss-card Lister keyword routes to the binds tab too
    await routeClick(page, '#boss-detail-panel [data-su-route="Lister the Tormentor"]');
    const s = await bindCardState(page);
    expect(s.activeTab).toBe('binds');
    expect(s.open).toBe(true);
    expect(s.text).toMatch(/Lister/);
  });

  test('no console errors across the SU keyword routing flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(URL);
    await page.waitForTimeout(800);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('ref'));
    await page.waitForTimeout(150);
    await routeClick(page, '[data-su-route="Lister the Tormentor"]');
    await page.evaluate(() => (window as any).openBindSUByName('The Smith'));
    await page.waitForTimeout(300);
    expect(errors).toEqual([]);
  });
});
