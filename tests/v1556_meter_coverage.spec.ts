import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1556 — THE METER PROMISES 160 HUNTS AND THE APP CAN GUIDE 125.
//
// Same class as the hero-vs-meter split (v1555), one layer out. `total` is the GAME's denominator —
// chronTotal 403, the in-game Chronicle's own count — so the caption reads "160 grails still out
// there". True of Diablo. But 35 of those 160 have no card and no source in this app: the
// internal-typo aliases, the 8 Rainbow Facet rows, quest uniques and RotW customs that the v663
// comment already names. They cannot be hunted, ranked or ticked here.
//
// Measured on his data: found 243, total 403, left 160, missing-with-cards 125, all 125 with a
// usable source. So the number beside the promise was 35 larger than the promise could keep.

const ORIGIN = 'http://tvd.console.test';
const UI = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');
const BOARD = 'file://' + path.resolve(__dirname, '..', 'bible.html');

async function meter(page: any, grail: any) {
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI }));
  await page.route((u: URL) => u.pathname.startsWith('/api/'), (r: any) => r.abort());
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.evaluate((g: any) => {
    document.body.dataset.view = 'sessions';
    // the console reads through lsFork (v1478 — the storage world arrives as DATA from the board),
    // so seed the route as "bare" and then the bare key, rather than guessing the prefix
    localStorage.setItem('d2r_lsrRoute', JSON.stringify({ prefix: '' }));
    localStorage.setItem('d2r_forgeSummary', JSON.stringify({ grail: g }));
  }, grail);
  // NO optional chaining here: if the seam is missing the test must FAIL, not quietly render
  // nothing and blame the caption.
  await page.evaluate(() => (window as any)._hubMeter());
  await page.waitForTimeout(300);
  return page.evaluate(() => (document.getElementById('hub-meter') || document.body).textContent || '');
}

test.describe('v1556 — the meter says what the app can actually help with', () => {
  test('★ the board exports how many missing grails are HUNTABLE', async ({ page }) => {
    await page.goto(BOARD);
    await page.waitForTimeout(2000);
    const r = await page.evaluate(() => {
      const w: any = window;
      const s = w.funiScan();
      const huntable = (s.missing || []).filter((x: any) => !!w._pickSrc(x.sources)).length;
      return { found: s.found, chronTotal: s.chronTotal, carded: s.total,
        missing: (s.missing || []).length, huntable,
        gap: (s.chronTotal - s.found) - huntable };
    });
    expect(r.huntable, 'every missing item with a card must have a source').toBe(r.missing);
    expect(r.gap, 'the game counts more still-out-there than this app has cards for')
      .toBeGreaterThan(0);
    expect(r.chronTotal).toBeGreaterThan(r.carded);
  });

  test('★ the caption names the app coverage when it is short of the game count', async ({ page }) => {
    const txt = await meter(page, { found: 243, total: 403, carded: 368, huntable: 125 });
    expect(txt, 'his real grail still leads').toContain('243');
    expect(txt).toContain('403');
    expect(txt, "the game's remainder is still stated").toContain('160');
    expect(txt, 'and so is what this app can guide').toContain('125');
    expect(txt).toContain('known hunt');
  });

  test('★ when the app covers everything it says nothing extra', async ({ page }) => {
    // a caveat that fires when there is no caveat is noise, and noise is what he skips
    const txt = await meter(page, { found: 390, total: 403, carded: 403, huntable: 13 });
    expect(txt).toContain('13');
    expect(txt).not.toContain('known hunt');
  });

  test('an old summary with no huntable field still renders the way it always did', async ({ page }) => {
    // forgeSummary is written by the BOARD; a console newer than the board must not break
    const txt = await meter(page, { found: 243, total: 403 });
    expect(txt).toContain('160');
    expect(txt).toContain('60%');
    expect(txt).not.toContain('known hunt');
  });

  test('the percentage still uses the game denominator, not the carded one', async ({ page }) => {
    // 243/403 = 60%. Against the 368 cards it would read 66% and overstate his grail.
    const txt = await meter(page, { found: 243, total: 403, carded: 368, huntable: 125 });
    expect(txt).toContain('60%');
    expect(txt).not.toContain('66%');
  });
});
