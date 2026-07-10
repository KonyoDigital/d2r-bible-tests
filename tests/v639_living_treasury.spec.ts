import { test, expect } from './_net_stub';
import * as path from 'path';
const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v639 — THE LIVING TREASURY motion pass: keywords/items loot-pop, living gold progress bars,
// engraved title reveals, ember sub-tabs — site-wide incl. F-Uniques/F-Sets. GPU-only, and
// EVERYTHING dies under prefers-reduced-motion (the v605 doctrine).

test('the motion system is wired: loot-pop on keyword anchors, bar sweep+shimmer, title veins, ember tabs — and reduced-motion kills it all', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(() => {
    const css = document.getElementById('v639-polish')?.textContent || '';
    const probe = document.querySelector('[data-arttip]');
    const cs = probe ? getComputedStyle(probe) : null;
    // the chronicle bar fill carries the sweep-in animation
    (window as any).switchTab && (window as any).switchTab('runes');
    try { (window as any).renderRunewordChronicle(); } catch (e) {}
    const fill = document.querySelector('.rwc-bar > span');
    const fillCs = fill ? getComputedStyle(fill) : null;
    const tab = document.querySelector('.tabs .tab.active');
    return {
      block: !!css && /v639BarIn/.test(css) && /v639Breathe/.test(css) && /v639Ember/.test(css),
      reducedKill: /prefers-reduced-motion:\s*reduce/.test(css) && /animation:\s*none\s*!important/.test(css),
      popTransition: !!(cs && /transform/.test(cs.transition)),
      barAnimated: !!(fillCs && fillCs.animationName === 'v639BarIn'),
      activeTab: !!tab,
    };
  });
  expect(r.block).toBe(true);
  expect(r.reducedKill).toBe(true);
  expect(r.popTransition).toBe(true);
  expect(r.barAnimated).toBe(true);
  expect(r.activeTab).toBe(true);
});

test('no horizontal overflow introduced on the heavy tabs (main / forge / F-Uniques / F-Sets)', async ({ page }) => {
  await page.goto(URL); await page.waitForTimeout(1500);
  const r = await page.evaluate(async () => {
    const w: any = window;
    const out: any = {};
    for (const t of ['main', 'forge', 'funi', 'fsets']) {
      try { w.switchTab(t); } catch (e) {}
      await new Promise((res) => setTimeout(res, 250));
      out[t] = document.documentElement.scrollWidth <= document.documentElement.clientWidth + 2;
    }
    return out;
  });
  ['main','forge','funi','fsets'].forEach((t) => expect((r as any)[t]).toBe(true));
});
