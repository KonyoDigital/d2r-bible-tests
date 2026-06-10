import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v162 — the floating nav-widget compass FAB is moved from the bottom-LEFT corner to
// the bottom-RIGHT, stacked ABOVE the ? help-btn so the two gold circles never overlap
// (Konyo: "the compass on the left corner ... should be moved to the right corner side
// and also upgrade the art on it make it more cool animated looking compass style").
// The flat 🧭 emoji is replaced by an inline SVG compass face (gold ring + ticks + a
// red/cream needle that slowly "searches" via @keyframes navCompassSpin). The panel
// still opens within the viewport. Additive UI — every nav chip/handler is untouched.
// Also asserts the static "How to use" help list now documents the D + R shortcuts.
test.describe('v162 nav compass relocated bottom-right + animated', () => {
  test.beforeEach(async ({ page }) => {
    // suppress the rare first-visit routine-bar pulse (a transient z9999 widget that
    // briefly covers the whole bottom-right corner — including the ? help-btn) so we
    // measure the compass in its persistent, returning-visitor state
    await page.addInitScript(() => { try { localStorage.setItem('routineBarSeen', '1'); } catch (e) {} });
    await page.goto(URL);
    await page.waitForTimeout(700);
  });

  test('the nav-widget is pinned to the bottom-RIGHT (no longer bottom-left)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = document.getElementById('nav-widget')!;
      const fab = document.getElementById('nav-fab')!;
      const cs = getComputedStyle(w);
      const rect = w.getBoundingClientRect();
      const fr = fab.getBoundingClientRect();
      return {
        exists: !!w,
        // the FAB hugs the RIGHT edge (right gutter), not the left
        gapFromRight: Math.round(window.innerWidth - fr.right),
        gapFromLeft: Math.round(fr.left),
        // the whole widget box sits in the right half of the viewport
        inRightHalf: rect.left > window.innerWidth / 2,
        alignEnd: cs.alignItems === 'flex-end',
      };
    });
    expect(r.exists).toBe(true);
    expect(r.gapFromRight).toBeLessThan(40);          // pinned to the right edge
    expect(r.gapFromLeft).toBeGreaterThan(500);       // far from the left (was left:20px)
    expect(r.inRightHalf).toBe(true);
    expect(r.alignEnd).toBe(true);
  });

  test('the FAB renders an animated SVG compass (not the flat emoji)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const fab = document.getElementById('nav-fab')!;
      const svg = fab.querySelector('svg.nav-compass');
      const needle = fab.querySelector('.nc-needle') as Element;
      return {
        hasSvg: !!svg,
        noEmoji: !(fab.textContent || '').includes('🧭'),
        hasNeedle: !!needle,
        hasRing: !!fab.querySelector('.nc-ring'),
        animates: /navCompassSpin/.test(getComputedStyle(needle).animationName),
      };
    });
    expect(r.hasSvg).toBe(true);
    expect(r.noEmoji).toBe(true);
    expect(r.hasNeedle).toBe(true);
    expect(r.hasRing).toBe(true);
    expect(r.animates).toBe(true);
  });

  test('the compass FAB does NOT overlap the ? help-btn', async ({ page }) => {
    const r = await page.evaluate(() => {
      const fab = document.getElementById('nav-fab')!.getBoundingClientRect();
      const help = document.querySelector('.help-btn')!.getBoundingClientRect();
      const overlap = !(fab.bottom <= help.top || fab.top >= help.bottom
        || fab.right <= help.left || fab.left >= help.right);
      return { overlap, fabBottom: Math.round(fab.bottom), helpTop: Math.round(help.top) };
    });
    expect(r.overlap).toBe(false);
    // the FAB sits ABOVE the help button (its bottom edge is above the help's top)
    expect(r.fabBottom).toBeLessThanOrEqual(r.helpTop + 1);
  });

  test('the nav panel still opens and stays within the viewport', async ({ page }) => {
    await page.locator('#nav-fab').click();
    await page.waitForTimeout(350);
    const r = await page.evaluate(() => {
      const w = document.getElementById('nav-widget')!;
      const panel = document.getElementById('nav-panel')!;
      const pr = panel.getBoundingClientRect();
      return {
        open: w.classList.contains('open'),
        leftIn: pr.left >= 0,
        rightIn: pr.right <= window.innerWidth + 1,
        topIn: pr.top >= 0,
        hasChips: panel.querySelectorAll('.nav-chip').length > 0,
      };
    });
    expect(r.open).toBe(true);
    expect(r.leftIn).toBe(true);
    expect(r.rightIn).toBe(true);
    expect(r.topIn).toBe(true);
    expect(r.hasChips).toBe(true);
  });

  test('navigation still works: clicking a chip switches tab', async ({ page }) => {
    await page.locator('#nav-fab').click();
    await page.waitForTimeout(300);
    await page.locator('.nav-chip[data-nav="runes"]').click();
    await page.waitForTimeout(300);
    const active = await page.evaluate(() =>
      document.querySelector('.tab.active')?.getAttribute('data-tab'));
    expect(active).toBe('runes');
  });

  test('the static "How to use" help now documents the D and R shortcuts', async ({ page }) => {
    const r = await page.evaluate(() => {
      const txt = document.body.textContent || '';
      return {
        dockDoc: /toggle the MF \/ Players dock/i.test(txt),
        routineDoc: /toggle the routine-status widget/i.test(txt),
      };
    });
    expect(r.dockDoc).toBe(true);
    expect(r.routineDoc).toBe(true);
  });

  test('no console errors with the relocated animated compass', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(URL);
    await page.waitForTimeout(800);
    await page.locator('#nav-fab').click();
    await page.waitForTimeout(300);
    expect(errors).toEqual([]);
  });
});
