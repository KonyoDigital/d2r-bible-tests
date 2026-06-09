import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v159 — the "complete grail-hunting reference…" tagline is relocated (at parse time)
// out of the top masthead into a top caption row of the bottom command dock (Konyo:
// "this can also be on the bottom. move it"). The "Konyo's D2R Farming Bible" wordmark
// gets an animated gold sheen, and the segmented tab bar gains a breathing gold glow +
// a flowing animated underline on the active tab ("make cooler and animated more").
// ZERO copy/handler change: the tagline element keeps its class + verbatim text, the
// h-title still reads the wordmark, every tab/id is untouched.
test.describe('v159 tagline-to-dock + animated masthead title + livelier tabs', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(800);
  });

  test('the tagline is moved INTO the dock (verbatim) and gone from the masthead', async ({ page }) => {
    const r = await page.evaluate(() => {
      const dock = document.getElementById('control-dock')!;
      const tagline = document.querySelector('.masthead-tagline') as HTMLElement;
      return {
        taglineExists: !!tagline,
        taglineInDock: dock.contains(tagline),
        inDockTagline: !!dock.querySelector('.dock-tagline .masthead-tagline'),
        text: (tagline?.textContent || '').trim(),
        // the controls relocated in v158 are still in the dock alongside the tagline
        mfInDock: dock.contains(document.getElementById('mf')),
        // the tagline no longer lives inside the top masthead
        taglineStillInMasthead: !!document.querySelector('.masthead .masthead-tagline'),
      };
    });
    expect(r.taglineExists).toBe(true);
    expect(r.taglineInDock).toBe(true);
    expect(r.inDockTagline).toBe(true);
    expect(r.text).toContain('grail-hunting reference');
    expect(r.text).toContain('personal wishlist tracking');
    expect(r.mfInDock).toBe(true);
    expect(r.taglineStillInMasthead).toBe(false);
  });

  test('the "Konyo\'s D2R Farming Bible" wordmark has an animated gold-gradient sheen', async ({ page }) => {
    const r = await page.evaluate(() => {
      const title = document.querySelector('.masthead .h-title') as HTMLElement;
      const cs = getComputedStyle(title);
      return {
        text: (title.textContent || '').trim(),
        hasGradient: /gradient/.test(cs.backgroundImage),
        fillTransparent: (cs.webkitTextFillColor || (cs as any).WebkitTextFillColor || '').includes('rgba(0, 0, 0, 0)')
          || cs.color === 'rgba(0, 0, 0, 0)',
        animatesSheen: /v159TitleSheen/.test(cs.animationName),
        // the inline emblem is a replaced <img> — it renders regardless of the text clip
        emblemPresent: !!title.querySelector('.masthead-art'),
      };
    });
    expect(r.text).toContain("Konyo's D2R Farming Bible");
    expect(r.hasGradient).toBe(true);
    expect(r.fillTransparent).toBe(true);
    expect(r.animatesSheen).toBe(true);
    expect(r.emblemPresent).toBe(true);
  });

  test('the tab bar breathes (capsule glow) and the active tab has a flowing underline', async ({ page }) => {
    const r = await page.evaluate(() => {
      const tabs = document.querySelector('.tabs') as HTMLElement;
      const active = document.querySelector('.tabs .tab.active') as HTMLElement;
      return {
        capsuleAnimates: /v159TabsGlow/.test(getComputedStyle(tabs).animationName),
        sheenAnimates: /v159TabsSheen/.test(getComputedStyle(tabs, '::before').animationName),
        underlineAnimates: /v159TabUnderline/.test(getComputedStyle(active, '::after').animationName),
      };
    });
    expect(r.capsuleAnimates).toBe(true);
    expect(r.sheenAnimates).toBe(true);
    expect(r.underlineAnimates).toBe(true);
  });

  test('the relocated controls + tagline keep the dock pinned to the bottom', async ({ page }) => {
    const r = await page.evaluate(() => {
      const dock = document.getElementById('control-dock') as HTMLElement;
      const dr = dock.getBoundingClientRect();
      return {
        position: getComputedStyle(dock).position,
        bottomGap: Math.round(window.innerHeight - dr.bottom),
        bodyPadBottom: parseInt(getComputedStyle(document.body).paddingBottom) || 0,
      };
    });
    expect(r.position).toBe('fixed');
    expect(r.bottomGap).toBeLessThanOrEqual(2);
    expect(r.bodyPadBottom).toBeGreaterThanOrEqual(60);
  });

  test('no console errors with the relocated tagline + animated masthead', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(URL);
    await page.waitForTimeout(900);
    expect(errors).toEqual([]);
  });
});
