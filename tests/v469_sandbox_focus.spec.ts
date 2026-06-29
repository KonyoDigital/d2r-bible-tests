// v469 — Crafted "Create Now" SANDBOX FOCUS MODE: when the preview sandbox is active AND it already completes a
// recipe (something in Make now), the "Almost there — what to grab next" list is hidden (replaced by a small
// focus note) so a single-recipe what-if isn't cluttered by near-misses that re-use the same simulated
// ingredients. The non-preview dashboard is unchanged.
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

test.describe('v469 sandbox focus mode', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForFunction(() => (window as any).renderCreateNow && (window as any).buildTopPicks);
    await page.evaluate(() => { (window as any).switchTab && (window as any).switchTab('tools'); });
    await page.waitForTimeout(600);
  });

  test('sandbox ON + a complete recipe → "Almost there" hidden, focus note shown', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w.buildTopPicks = function(){ return {
        makeNow: [{ kind:'craft', name:'Caster Amulet', slot:'Amulet', base:'Amulet', gem:'Perfect Amethyst', rune:'Ral' }],
        afterCubing: [],
        close: [{ kind:'craft', name:'Caster Ring', slot:'Ring', base:'Ring', gem:'Perfect Amethyst', rune:'Ral', need:'magic Ring base', awayN:1 }],
      }; };
      w.previewStash = { runes:{}, gems:{}, bases:{}, jewels:{} };   // sandbox ON
      w.renderCreateNow();
      const on = (document.getElementById('create-now') || {}).innerHTML || '';
      w.previewStash = null;                                          // sandbox OFF
      w.renderCreateNow();
      const off = (document.getElementById('create-now') || {}).innerHTML || '';
      return { on, off };
    });
    // focus mode: Make-now shows, Almost-there hidden, note present
    expect(r.on).toContain('Make now');
    expect(r.on).toContain('Caster Amulet');
    expect(r.on).not.toContain('Almost there');
    expect(r.on).toContain('Sandbox focus');
    // sandbox off: Almost-there returns
    expect(r.off).toContain('Almost there');
    expect(r.off).toContain('Caster Ring');
    expect(r.off).not.toContain('Sandbox focus');
  });

  test('sandbox ON but NOTHING makeable → Almost there still shows (focus only kicks in once a recipe completes)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      w.buildTopPicks = function(){ return {
        makeNow: [],
        afterCubing: [],
        close: [{ kind:'craft', name:'Caster Ring', slot:'Ring', base:'Ring', gem:'Perfect Amethyst', rune:'Ral', need:'magic Ring base', awayN:1 }],
      }; };
      w.previewStash = { runes:{}, gems:{}, bases:{}, jewels:{} };
      w.renderCreateNow();
      return (document.getElementById('create-now') || {}).innerHTML || '';
    });
    expect(r).toContain('Almost there');   // nothing in Make-now yet → keep showing what to grab
    expect(r).not.toContain('Sandbox focus');
  });
});
