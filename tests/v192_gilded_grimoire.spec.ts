// v192 — "Gilded Grimoire" design layer lockdown (CSS-only ship).
// Verifies the appended style block exists and its test-safety invariants hold:
// decorative overlays NEVER intercept pointer events (the same class of bug as the
// HUD-badge click-interception fix), one-shot load animations end at identity, and
// prefers-reduced-motion kills the masthead shimmer.
import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v192 gilded grimoire design layer', () => {
  test('style block present; grain + ember overlays are pointer-events:none', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1500);
    const r = await page.evaluate(() => {
      const after = getComputedStyle(document.body, '::after');
      const before = getComputedStyle(document.body, '::before');
      return {
        block: !!document.getElementById('v192-gilded-grimoire-styles'),
        grainPE: after.pointerEvents,
        grainPos: after.position,
        emberPE: before.pointerEvents,
      };
    });
    expect(r.block).toBe(true);
    expect(r.grainPE).toBe('none');
    expect(r.grainPos).toBe('fixed');
    expect(r.emberPE).toBe('none');
  });

  test('masthead shimmer + Cinzel small-caps section titles applied', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(1500);
    const r = await page.evaluate(() => {
      const title = document.querySelector('.h-title') as HTMLElement;
      const secT = document.querySelector('.sec-h .sec-h-t') as HTMLElement;
      return {
        // the masthead sheen is the PRE-EXISTING v159TitleSheen (higher specificity
        // than the v192 layer — v192 deliberately does not duplicate it)
        shimmer: title ? getComputedStyle(title).animationName.includes('TitleSheen') : false,
        secCaps: secT ? getComputedStyle(secT).fontVariantCaps : '',
        secSerif: secT ? getComputedStyle(secT).fontFamily.toLowerCase().includes('cinzel') : false,
      };
    });
    expect(r.shimmer).toBe(true);
    expect(r.secCaps).toBe('small-caps');
    expect(r.secSerif).toBe(true);
  });

  test('load animations are one-shot and settle at identity (clicks stay stable)', async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(2200); // longest rise = .6s + .15s delay — long settled by now
    const r = await page.evaluate(() => {
      const header = document.querySelector('.header') as HTMLElement;
      const cs = getComputedStyle(header);
      return { opacity: cs.opacity, transform: cs.transform };
    });
    expect(r.opacity).toBe('1');
    expect(['none', 'matrix(1, 0, 0, 1, 0, 0)']).toContain(r.transform);
  });

  test('prefers-reduced-motion disables the load rise + shimmer stays harmless', async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto(URL);
    await page.waitForTimeout(1200);
    const r = await page.evaluate(() => {
      const header = document.querySelector('.header') as HTMLElement;
      return { anim: getComputedStyle(header).animationName, opacity: getComputedStyle(header).opacity };
    });
    expect(r.anim).toBe('none');
    expect(r.opacity).toBe('1');
  });

  test('no console errors with the design layer active', async ({ page }) => {
    const errs: string[] = [];
    page.on('pageerror', e => errs.push(e.message));
    page.on('console', m => {
      if (m.type() === 'error' && !/net::|Failed to load resource/.test(m.text())) errs.push(m.text());
    });
    await page.goto(URL);
    await page.waitForTimeout(2000);
    await page.evaluate(() => (window as any).switchTab('binds'));
    await page.waitForTimeout(600);
    await page.evaluate(() => (window as any).switchTab('bosses'));
    await page.waitForTimeout(600);
    expect(errs).toEqual([]);
  });
});
