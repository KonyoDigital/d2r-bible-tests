import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// The console is served from a VIRTUAL http origin rather than file://. On file:// the browser kills
// a relative fetch before Playwright's routing ever sees it, so every assertion about what the panel
// does with the route's answer would silently be testing the failure path instead. No real server is
// started — the HTML is fulfilled from disk and the API calls are fulfilled per test.
const ORIGIN = 'http://tvd.console.test';
const UI_HTML = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

// v1516 — 📜 THE CHRONICLE SWEEP panel, in the console's RECORD zone.
//
// It shows a QUOTE, not a tally. Konyo has been told a retro sweep of his reels costs 11 AI calls
// instead of 394 frame reads — this panel is where he CHECKS that instead of believing it. So the
// things worth locking are: the number is a price, the price comes from the route (never from the
// page's own arithmetic), and the panel never implies it read or wrote anything.

// v1596 — this fixture used to carry `pagesRead: 0, wouldRead: 11`, which was not a simplification
// but the BUG itself written down as an expectation: the route's cost probe answered None, so the
// sweep skipped its read stage and the quote billed only the classify lane. A real sweep pays for
// BOTH lanes, so the priced payload now looks like one — 11 classifies plus 14 page reads — and the
// panel is expected to say "at most", because the route prices every candidate run as readable.
const PRICED = {
  ok: true,
  totals: { reels: 4, framesSeen: 394, classified: 11, pagesRead: 14, refused: 0 },
  savedPct: 93.7, wouldRead: 25, wouldClassify: 11, wouldReadPages: 14,
  upperBound: true, boundWhy: 'prices every candidate run as a readable page',
  insteadOf: 394, spent: 0,
  reels: [
    { reel: 's_1784984019250_95276', runs: 6, classified: 6, pages: 8 },
    { reel: 's_1785078127173_28278', runs: 4, classified: 4, pages: 6 },
  ],
};

async function open(page: any, payload: any, status = 200) {
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI_HTML }));
  // every OTHER console call goes silent. A url-predicate rather than a '**/api/**' glob, because a
  // glob that also matches chronicle_scan wins the match and aborts the very call under test.
  await page.route((u: URL) => u.pathname.startsWith('/api/') && !u.pathname.includes('chronicle'),
    (r: any) => r.abort());
  await page.route((u: URL) => u.pathname === '/api/chronicle_scan', (r: any) =>
    r.fulfill({ status, contentType: 'application/json', body: JSON.stringify(payload) }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(400);
}

test.describe('v1516 — the Chronicle Sweep prices itself, honestly', () => {
  test('the panel lives in THE RECORD zone, where the chronicle of his runs already is', async ({ page }) => {
    await open(page, PRICED);
    const home = await page.evaluate(() => {
      const el = document.getElementById('hd-chron');
      const zone = el?.closest('section.zone');
      return { exists: !!el, banner: zone?.querySelector('.zone-banner')?.textContent || '' };
    });
    expect(home.exists).toBe(true);
    expect(home.banner).toContain('THE RECORD');
  });

  test('before it is asked, it promises nothing — and costs nothing', async ({ page }) => {
    await open(page, PRICED);
    const idle = await page.textContent('#chron-body');
    expect(idle).toMatch(/no model call/i);
    expect(await page.textContent('#chron-note')).toMatch(/costs nothing/i);
  });

  test('★ the price comes from the ROUTE, never from the page doing its own arithmetic', async ({ page }) => {
    // a page that recomputes the saving can drift from the engine that will actually spend the calls
    await open(page, { ...PRICED, savedPct: 42.0, wouldRead: 7, wouldClassify: 3,
                       wouldReadPages: 4, insteadOf: 100 });
    await page.click('#chron-scan');
    await page.waitForTimeout(250);
    const txt = await page.textContent('#chron-body');
    expect(txt).toContain('42');
    expect(txt).toContain('7');
    expect(txt).not.toContain('93.7');
  });

  test('the real numbers render as a price with its units named', async ({ page }) => {
    await open(page, PRICED);
    await page.click('#chron-scan');
    await page.waitForTimeout(250);
    const txt = (await page.textContent('#chron-body')) || '';
    expect(txt).toContain('93.7');
    expect(txt).toContain('25');
    expect(txt).toContain('394');
    expect(txt).toMatch(/AI calls it/);           // 25 is calls, not items found
    expect(txt).toMatch(/frames across/);         // 394 is frames, not a tally
    expect(txt).not.toMatch(/found|grail|tallied/i);   // ★ never reads as a result
  });

  test('★ v1596 — the headline is shown as a CEILING, with both lanes broken out', async ({ page }) => {
    // The route prices every candidate run as though it were readable, so the figure it returns is
    // an upper bound. A bound printed as a flat number is read as a bill, and the whole purpose of
    // this panel is that he does not have to take the number on faith.
    await open(page, PRICED);
    await page.click('#chron-scan');
    await page.waitForTimeout(250);
    const txt = (await page.textContent('#chron-body')) || '';
    expect(txt, 'the figure must be marked as a ceiling, not a flat price').toMatch(/≤|at most/);
    expect(txt, 'the classify lane must be named').toContain('11');
    expect(txt, 'and the READ lane — the half the old quote could not count at all').toContain('14');
    expect(txt).toMatch(/to read a page/);
  });

  test('★ v1596 — an older payload without the breakdown degrades, it does not print "undefined"',
    async ({ page }) => {
      // The console and the route ship together, but a stale tab against a new server (or the
      // reverse) is a real state on his machine — and "undefined AI calls" is the kind of thing he
      // reports as the panel being broken.
      const { wouldClassify, wouldReadPages, upperBound, boundWhy, ...older } = PRICED as any;
      await open(page, older);
      await page.click('#chron-scan');
      await page.waitForTimeout(250);
      const txt = (await page.textContent('#chron-body')) || '';
      expect(txt).not.toMatch(/undefined/i);
      expect(txt).toContain('25');
    });

  test('after pricing it says what it did NOT do', async ({ page }) => {
    await open(page, PRICED);
    await page.click('#chron-scan');
    await page.waitForTimeout(250);
    const note = (await page.textContent('#chron-note')) || '';
    expect(note).toMatch(/0 calls spent/);
    expect(note).toMatch(/nothing written/);
  });

  test('per-reel rows show the grouping that produced the price', async ({ page }) => {
    await open(page, PRICED);
    await page.click('#chron-scan');
    await page.waitForTimeout(250);
    const rows = await page.$$eval('.chron-reels .cr', (n: any[]) => n.map((x) => x.textContent));
    expect(rows).toHaveLength(2);
    expect(rows[0]).toContain('6');
  });

  test('★ no reels is said plainly, never dressed as a zero saving', async ({ page }) => {
    await open(page, { ok: true, reels: [], totals: { reels: 0, framesSeen: 0, classified: 0 },
                       note: 'no sealed reels yet' });
    await page.click('#chron-scan');
    await page.waitForTimeout(250);
    const txt = (await page.textContent('#chron-body')) || '';
    expect(txt).toMatch(/no sealed reels/i);
    expect(txt).not.toContain('%');
  });

  test('★ an unreachable engine says so — it never implies there is nothing to sweep', async ({ page }) => {
    await open(page, { ok: false, why: 'chronicle_retro unavailable' });
    await page.click('#chron-scan');
    await page.waitForTimeout(250);
    const txt = (await page.textContent('#chron-body')) || '';
    expect(txt).toMatch(/could not price/i);
    expect(txt).toContain('chronicle_retro unavailable');
  });

  test('the button re-arms after a failure so he is never stuck', async ({ page }) => {
    await open(page, { ok: false, why: 'boom' });
    await page.click('#chron-scan');
    await page.waitForTimeout(250);
    expect(await page.isDisabled('#chron-scan')).toBe(false);
  });
});
