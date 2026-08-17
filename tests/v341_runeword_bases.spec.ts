// v1754 — through the shared net stub. This spec LISTENS for console errors, and a console
// error array collects RESOURCE failures as well as JS faults. bible.html's only external
// requests are five Google Fonts URLs; on a runner with slow or blocked egress they fail,
// land in the array, and the spec goes red on the weather rather than on the code.
import { test, expect } from './_net_stub';

// v341.29/.30/.31 — Runeword Base Browser: grey (normal-quality) base names with a rich socket/
// runeword floating tooltip + HD base art; runeword tooltips lead with their top-tier base image.
test.describe('runeword base browser', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('file://' + process.cwd() + '/bible.html');
    await page.waitForFunction(() => (window as any)._arttipResolve && (window as any).RW_BASE_INDEX);
  });

  test('base names are grey normal-quality, not white', async ({ page }) => {
    const c = await page.evaluate(() => {
      (window as any).switchTab('tools'); (window as any).renderRwBases();
      const el = document.querySelector('.rwb-base') as HTMLElement;
      return el ? getComputedStyle(el).color : '';
    });
    // grey ~ rgb(168,173,184); definitely NOT the old near-white #f4f4f4 (244,244,244)
    expect(c).not.toBe('rgb(244, 244, 244)');
    const m = c.match(/\d+/g)!.map(Number);
    expect(m[0]).toBeLessThan(220); expect(Math.abs(m[0] - m[2])).toBeLessThan(40); // greyish, slightly cool
  });

  test('a base resolves a rich tooltip with sockets + its runewords + HD art', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any;
      const t = w._arttipResolve('Archon Plate');
      return { rich: !!(t && t.rich), sock: /socket|runeword base/i.test(t?.desc || ''),
               rws: /Enigma/.test(t?.desc || ''), art: !!w.artUrl('Archon Plate') };
    });
    expect(r.rich).toBe(true); expect(r.sock).toBe(true); expect(r.rws).toBe(true); expect(r.art).toBe(true);
  });

  test('runeword tooltip carries its top-tier base art (Enigma → Archon Plate)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const w = window as any; const e = w._arttipResolve('Enigma');
      return { name: e?.artName, hasArt: !!w.artUrl(e?.artName), spirit: w.artUrl(w._arttipResolve('Spirit')?.artName) };
    });
    expect(r.name).toBe('Archon Plate'); expect(r.hasArt).toBe(true); expect(r.spirit).toBeTruthy();
  });

  test('base rows render art + are clickable, no console errors', async ({ page }) => {
    const errs: string[] = [];
    page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    const r = await page.evaluate(() => {
      (window as any).switchTab('tools'); (window as any).renderRwBases();
      const rows = [...document.querySelectorAll('.rwb-base')];
      return { withArt: rows.filter(el => el.querySelector('.d2art-wrap, img')).length, total: rows.length,
               clickable: rows.every(el => (el as HTMLElement).getAttribute('onclick')) };
    });
    expect(r.total).toBeGreaterThan(10); expect(r.withArt).toBe(r.total); expect(r.clickable).toBe(true);
    expect(errs.length).toBe(0);
  });
});
