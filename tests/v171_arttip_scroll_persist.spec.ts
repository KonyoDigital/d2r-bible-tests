import { test, expect } from '@playwright/test';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v171 — the floating #arttip hover popup ("art cursor floating window") was being
// blanked by a trailing scroll event. v169 had added a capture-phase scroll listener
// that dismissed the tip on EVERY scroll, to kill an orphaned tip after a click
// re-render. But the site uses global scroll-behavior:smooth, and macOS trackpad
// inertial (momentum) scrolling emits a long tail of scroll events AFTER the finger
// lifts. So: the user scrolled to a grail tile, the tip got set during a lull, then a
// trailing momentum scroll stripped its .on class -> the popup never appeared ("not
// loading"). The v171 fix narrows the scroll-dismiss to fire ONLY when the hovered
// host is actually orphaned (disconnected / hidden) -- mirroring the mousemove guard --
// so a benign scroll over a still-visible element no longer blanks a valid tip.
// Additive/behavioral: the click-dismiss + mousemove orphan guard are untouched.
test.describe('v171 #arttip survives a benign (momentum) scroll, dismisses only when orphaned', () => {
  test.beforeEach(async ({ page }) => {
    // tall viewport so the grail tiles are in view with no competing smooth scroll
    await page.setViewportSize({ width: 1280, height: 2000 });
    await page.goto(URL);
    await page.waitForTimeout(900);
    await page.evaluate(() => (window as any).switchTab && (window as any).switchTab('bosses'));
    await page.waitForTimeout(300);
    await page.evaluate(() => (window as any).openBossDetail && (window as any).openBossDetail('duriel'));
    await page.waitForTimeout(1500); // let openBossDetail's own smooth scroll settle
  });

  async function hoverTile(page: any) {
    const r = await page.evaluate(() => {
      const el = document.querySelector('#boss-detail-panel .gbc-grail-item[data-arttip="Wizardspike"]') as HTMLElement;
      const b = el.getBoundingClientRect();
      return { x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2) };
    });
    await page.mouse.move(r.x - 50, r.y);
    await page.waitForTimeout(50);
    await page.mouse.move(r.x, r.y);
    await page.waitForTimeout(120);
  }

  test('hovering a grail tile opens the rich card', async ({ page }) => {
    await hoverTile(page);
    const s = await page.evaluate(() => {
      const t = document.getElementById('arttip')!;
      return { on: t.classList.contains('on'), rich: t.classList.contains('tip-rich'), name: (t.querySelector('.att-name') as HTMLElement).textContent };
    });
    expect(s.on).toBe(true);
    expect(s.rich).toBe(true);
    expect(s.name).toBe('Wizardspike');
  });

  test('a trailing (momentum) scroll over a still-visible tile does NOT blank the tip', async ({ page }) => {
    await hoverTile(page);
    expect(await page.evaluate(() => document.getElementById('arttip')!.classList.contains('on'))).toBe(true);
    // simulate the macOS inertial-scroll tail: scroll events fire WITHOUT moving the
    // mouse or removing the hovered element. Pre-v171 each of these stripped .on.
    const stillOn = await page.evaluate(() => {
      for (let i = 0; i < 5; i++) { window.dispatchEvent(new Event('scroll')); document.dispatchEvent(new Event('scroll', { bubbles: true })); }
      return document.getElementById('arttip')!.classList.contains('on');
    });
    expect(stillOn).toBe(true); // the regression-locked v171 behavior
  });

  test('a scroll that ORPHANS the host (hidden / removed) still dismisses the tip', async ({ page }) => {
    await hoverTile(page);
    expect(await page.evaluate(() => document.getElementById('arttip')!.classList.contains('on'))).toBe(true);
    const dismissed = await page.evaluate(() => {
      const el = document.querySelector('#boss-detail-panel .gbc-grail-item[data-arttip="Wizardspike"]') as HTMLElement;
      el.style.display = 'none'; // orphan it (offsetParent === null)
      window.dispatchEvent(new Event('scroll'));
      return !document.getElementById('arttip')!.classList.contains('on');
    });
    expect(dismissed).toBe(true);
  });

  test('a click still dismisses the tip (v169 orphan-after-click guard intact)', async ({ page }) => {
    await hoverTile(page);
    expect(await page.evaluate(() => document.getElementById('arttip')!.classList.contains('on'))).toBe(true);
    await page.evaluate(() => document.body.dispatchEvent(new MouseEvent('click', { bubbles: true })));
    await page.waitForTimeout(50);
    expect(await page.evaluate(() => document.getElementById('arttip')!.classList.contains('on'))).toBe(false);
  });

  test('no console errors across the scroll-persist hover flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(e.message));
    await hoverTile(page);
    await page.evaluate(() => { for (let i = 0; i < 5; i++) window.dispatchEvent(new Event('scroll')); });
    await page.waitForTimeout(100);
    expect(errors).toEqual([]);
  });
});
