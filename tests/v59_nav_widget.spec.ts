import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v59 — floating navigation compass widget. Clicking an item drops you deep in a
// tab; the sticky tab bar is then off-screen, so changing tabs meant scrolling
// all the way back up. This adds a persistent bottom-right compass (🧭) that, at
// any scroll depth, expands to one-tap chips for every tab + a "Back to top"
// button. Chips are built FROM the existing .tabs buttons (single source of
// truth) and the active chip stays in sync with whatever switched the tab
// (header click, hash route, or the widget itself).
test.describe('v59 nav compass widget', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1200);
  });

  test('widget mounts: FAB + one chip per tab (in sync with .tabs) + back-to-top', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = document.getElementById('nav-widget');
      const fab = document.getElementById('nav-fab');
      const tabNames = [...document.querySelectorAll('.tabs .tab')].map(t => (t as HTMLElement).dataset.tab);
      const chipNames = [...document.querySelectorAll('#nav-widget .nav-chip[data-nav]')]
        .map(c => c.getAttribute('data-nav'));
      return {
        hasWidget: !!w,
        hasFab: !!fab,
        fabIsCompass: (fab?.textContent || '').includes('🧭'),
        tabNames, chipNames,
        chipsMatchTabs: JSON.stringify(tabNames) === JSON.stringify(chipNames),
        hasBackToTop: !!document.querySelector('#nav-widget .nav-chip.nav-top'),
        // chips keep the tab emojis (Konyo likes them)
        firstChipKeepsIcon: (document.querySelector('#nav-widget .nav-chip .nav-ic')?.textContent || '').length > 0,
        noUndef: !/undefined/.test(w?.innerHTML || 'undefined'),
      };
    });
    expect(r.hasWidget).toBe(true);
    expect(r.hasFab).toBe(true);
    expect(r.fabIsCompass).toBe(true);
    expect(r.chipsMatchTabs).toBe(true);
    expect(r.chipNames.length).toBe(8);
    expect(r.hasBackToTop).toBe(true);
    expect(r.firstChipKeepsIcon).toBe(true);
    expect(r.noUndef).toBe(true);
  });

  test('FAB toggles the panel open/closed', async ({ page }) => {
    const closedAtStart = await page.evaluate(() => !document.getElementById('nav-widget')?.classList.contains('open'));
    expect(closedAtStart).toBe(true);
    await page.locator('#nav-fab').click();
    await page.waitForTimeout(150);
    await expect(page.locator('#nav-widget')).toHaveClass(/open/);
    // a chip must be visibly reachable when open
    await expect(page.locator('#nav-widget .nav-chip[data-nav="calc"]')).toBeVisible();
    await page.locator('#nav-fab').click();
    await page.waitForTimeout(150);
    await expect(page.locator('#nav-widget')).not.toHaveClass(/open/);
  });

  test('navTo switches tab, scrolls to top, closes panel, syncs active chip', async ({ page }) => {
    // scroll down so the scroll-to-top is observable. Use instant — html{scroll-behavior:smooth}
    // would otherwise animate setup scrolls and race the assertions.
    await page.evaluate(() => window.scrollTo({ top: 1200, behavior: 'instant' as ScrollBehavior }));
    await page.evaluate(() => (window as any).navTo('ref'));
    await page.waitForTimeout(700);
    const r = await page.evaluate(() => ({
      refTabActive: !!document.querySelector('.tab[data-tab="ref"].active'),
      refContentActive: !!document.querySelector('#tab-ref.active'),
      panelClosed: !document.getElementById('nav-widget')?.classList.contains('open'),
      scrolledTop: window.scrollY < 50,
      activeChip: document.querySelector('#nav-widget .nav-chip.active')?.getAttribute('data-nav'),
    }));
    expect(r.refTabActive).toBe(true);
    expect(r.refContentActive).toBe(true);
    expect(r.panelClosed).toBe(true);
    expect(r.scrolledTop).toBe(true);
    expect(r.activeChip).toBe('ref');
  });

  test('navTop returns to top from any scroll depth', async ({ page }) => {
    await page.evaluate(() => window.scrollTo({ top: 1500, behavior: 'instant' as ScrollBehavior }));
    expect(await page.evaluate(() => window.scrollY)).toBeGreaterThan(400);
    await page.evaluate(() => (window as any).navTop());
    await page.waitForTimeout(700);
    expect(await page.evaluate(() => window.scrollY)).toBeLessThan(50);
  });

  test('header tab click keeps the widget active-chip in sync', async ({ page }) => {
    await page.evaluate(() => (window as any).switchTab('tz'));
    await page.waitForTimeout(150);
    expect(await page.evaluate(() =>
      document.querySelector('#nav-widget .nav-chip.active')?.getAttribute('data-nav'))).toBe('tz');
    await page.evaluate(() => (window as any).switchTab('runes'));
    await page.waitForTimeout(150);
    expect(await page.evaluate(() =>
      document.querySelector('#nav-widget .nav-chip.active')?.getAttribute('data-nav'))).toBe('runes');
  });

  test('click-outside closes an open panel', async ({ page }) => {
    await page.locator('#nav-fab').click();
    await page.waitForTimeout(150);
    await expect(page.locator('#nav-widget')).toHaveClass(/open/);
    await page.locator('h1, .masthead, .header').first().click();
    await page.waitForTimeout(150);
    await expect(page.locator('#nav-widget')).not.toHaveClass(/open/);
  });

  test('keyboard: Enter on a focused chip navigates (role=button a11y)', async ({ page }) => {
    await page.locator('#nav-fab').click();
    await page.waitForTimeout(150);
    await page.locator('#nav-widget .nav-chip[data-nav="rotw"]').focus();
    await page.keyboard.press('Enter');
    await page.waitForTimeout(300);
    expect(await page.evaluate(() => !!document.querySelector('.tab[data-tab="rotw"].active'))).toBe(true);
    expect(await page.evaluate(() => document.getElementById('nav-widget')?.classList.contains('open'))).toBe(false);
  });

  test('ESC collapses an open nav panel', async ({ page }) => {
    await page.locator('#nav-fab').click();
    await page.waitForTimeout(150);
    await expect(page.locator('#nav-widget')).toHaveClass(/open/);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(150);
    await expect(page.locator('#nav-widget')).not.toHaveClass(/open/);
  });

  test('container is click-through (does not eat content clicks under its box); FAB stays interactive', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = document.getElementById('nav-widget')!;
      const fab = document.getElementById('nav-fab')!;
      const cs = (el: Element) => getComputedStyle(el).pointerEvents;
      // a point inside the widget's box but to the RIGHT of the FAB (the 188px-wide
      // dead zone that previously intercepted clicks on content underneath)
      const wr = w.getBoundingClientRect();
      const fr = fab.getBoundingClientRect();
      const probeX = Math.min(wr.right - 4, fr.right + 40);
      const probeY = fr.top + fr.height / 2;
      const hit = document.elementFromPoint(probeX, probeY);
      const fabHit = document.elementFromPoint(fr.left + fr.width / 2, fr.top + fr.height / 2);
      return {
        widgetPE: cs(w),
        fabPE: cs(fab),
        // the dead-zone point must fall through to page content, NOT the widget
        hitIsNotWidget: !(hit && w.contains(hit)),
        // the FAB center must still hit the FAB
        fabCenterHitsFab: !!fabHit && (fabHit === fab || fab.contains(fabHit)),
      };
    });
    expect(r.widgetPE).toBe('none');
    expect(r.fabPE).toBe('auto');
    expect(r.hitIsNotWidget).toBe(true);
    expect(r.fabCenterHitsFab).toBe(true);
  });

  test('clicking the bosses TAB returns to a FRESH home — no stuck farmed-item highlight', async ({ page }) => {
    // Konyo flow: open an item (sets the "now farming" bar + boss highlight), then click
    // the bosses tab → must land on the clean boss list, not the stuck filtered view.
    await page.evaluate(() => (window as any).navigateToItem('Harlequin Crest (Shako)', null));
    await page.waitForTimeout(300);
    await expect(page.locator('#active-item-bar')).toHaveClass(/show/);
    expect(await page.evaluate(() =>
      document.querySelectorAll('.boss-card.has-item, .boss-card.no-item').length)).toBeGreaterThan(0);
    // click the bosses tab (header)
    await page.locator('.tab[data-tab="bosses"]').click();
    await page.waitForTimeout(400);
    const r = await page.evaluate(() => ({
      barShown: document.getElementById('active-item-bar')?.classList.contains('show'),
      bossesActive: !!document.querySelector('.tab[data-tab="bosses"].active'),
      highlightedBosses: document.querySelectorAll('.boss-card.has-item, .boss-card.no-item').length,
    }));
    expect(r.barShown).toBe(false);
    expect(r.bossesActive).toBe(true);
    expect(r.highlightedBosses).toBe(0);
  });

  test('widget navTo("bosses") returns fresh and closes any open boss detail', async ({ page }) => {
    // open a boss detail card
    await page.evaluate(() => (window as any).openBossDetail('countess'));
    await page.waitForTimeout(300);
    await expect(page.locator('#boss-detail-overlay')).not.toHaveClass(/hidden/);
    // navigate to an item (sets the farming bar) then return home via the WIDGET chip
    await page.evaluate(() => (window as any).navigateToItem('Harlequin Crest (Shako)', null));
    await page.waitForTimeout(250);
    await page.evaluate(() => (window as any).navTo('bosses'));
    await page.waitForTimeout(400);
    const r = await page.evaluate(() => ({
      barShown: document.getElementById('active-item-bar')?.classList.contains('show'),
      bossDetailHidden: document.getElementById('boss-detail-overlay')?.classList.contains('hidden'),
      bossesActive: !!document.querySelector('.tab[data-tab="bosses"].active'),
    }));
    expect(r.barShown).toBe(false);
    expect(r.bossDetailHidden).toBe(true);
    expect(r.bossesActive).toBe(true);
  });

  test('no console errors across the widget flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.waitForTimeout(1200);
    await page.evaluate(() => {
      (window as any).toggleNavPanel();
      (window as any).navTo('calc');
      (window as any).navTo('runes');
      (window as any).navTop();
    });
    await page.waitForTimeout(200);
    expect(errors).toEqual([]);
  });
});
