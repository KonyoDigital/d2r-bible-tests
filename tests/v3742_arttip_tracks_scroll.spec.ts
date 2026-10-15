// v3742 — the floating item card (#arttip) GLUES to its anchor's rect (v643). The only things that
// re-checked that rect were MOUSE events (the mousemove self-correct, mouseout). On the console
// WebKit a wheel / PageDown / End / Space scroll fires NO mouse event, so the card hung at its old
// SCREEN position while the item slid away under it — the "stuck tooltip" seen on the Vault page.
// A programmatic window.scrollBy() reproduces that in Chromium: it fires 'scroll' but no pointer
// events (no real pointer is tracked for a synthetic mouseover), exactly like the WebKit case.
// RED before the fix (the card does not move with the item); GREEN after (the capture-phase scroll
// handler re-runs move() for a still-connected anchor). v171 is preserved — the card is never
// blanked while its anchor is on-screen, it simply follows; v171_arttip_scroll_persist.spec.ts stays green.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v3742 #arttip tracks its item through a mouse-less scroll', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 1000 });
    await page.goto(URL);
    await page.waitForTimeout(800);
  });

  test('the glued card re-anchors to its item when the page scrolls under a still pointer', async ({ page }) => {
    // open the card on a DETERMINISTIC anchor: artOr() yields a .d2art-wrap[aria-label] with an
    // <img>, parked at an absolute DOCUMENT position so it scrolls WITH the page, mid-viewport.
    const opened = await page.evaluate(() => {
      document.documentElement.style.scrollBehavior = 'auto';
      window.scrollTo(0, 0);
      const host = document.createElement('div');
      host.id = '_v3742host';
      host.style.cssText = 'position:absolute;top:450px;left:24px;z-index:1';
      host.innerHTML = (window as any).artOr("Andariel's Visage", '💀', 'sm');
      document.body.appendChild(host);
      const wrap = host.querySelector('.d2art-wrap[aria-label]') as HTMLElement;
      wrap.dispatchEvent(new MouseEvent('mouseover', { bubbles: true, clientX: 34, clientY: 460 }));
      return document.getElementById('arttip')!.classList.contains('on');
    });
    expect(opened).toBe(true); // the anchor opened the card, or nothing below measures anything

    await page.waitForTimeout(250); // let the open transition settle before measuring
    const before = await page.evaluate(() => {
      const tip = document.getElementById('arttip')!;
      const wrap = document.querySelector('#_v3742host .d2art-wrap[aria-label]') as HTMLElement;
      const tr = tip.getBoundingClientRect(), ar = wrap.getBoundingClientRect();
      return { on: tip.classList.contains('on'), tipTop: tr.top, anchorTop: ar.top };
    });
    expect(before.on).toBe(true);
    const delta0 = before.tipTop - before.anchorTop;

    await page.evaluate(() => window.scrollBy(0, 150));
    await page.waitForTimeout(250); // let the scroll event fire and the handler re-glue

    const after = await page.evaluate(() => {
      const tip = document.getElementById('arttip')!;
      const wrap = document.querySelector('#_v3742host .d2art-wrap[aria-label]') as HTMLElement;
      const tr = tip.getBoundingClientRect(), ar = wrap.getBoundingClientRect();
      return { on: tip.classList.contains('on'), tipTop: tr.top, anchorTop: ar.top, scrollY: window.scrollY };
    });
    const delta1 = after.tipTop - after.anchorTop;

    expect(after.scrollY).toBeGreaterThan(120);                      // the scroll really happened
    expect(before.anchorTop - after.anchorTop).toBeGreaterThan(120); // the item moved up in-viewport
    expect(after.on).toBe(true);                                     // not blanked (v171 preserved)
    // THE LAW: the card followed the item instead of hanging at its old screen position. Without the
    // fix tipTop is frozen while anchorTop fell ~150px, so |delta1 - delta0| ~ 150; the re-glue keeps
    // the vertical offset between card and item constant.
    expect(Math.abs(delta1 - delta0)).toBeLessThan(24);
  });
});
