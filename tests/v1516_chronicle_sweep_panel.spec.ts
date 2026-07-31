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

const PRICED = {
  ok: true,
  totals: { reels: 4, framesSeen: 394, classified: 11, pagesRead: 0, refused: 0 },
  savedPct: 97.2, wouldRead: 11, insteadOf: 394, spent: 0,
  reels: [
    { reel: 's_1784984019250_95276', runs: 6, classified: 6, pages: 0 },
    { reel: 's_1785078127173_28278', runs: 4, classified: 4, pages: 0 },
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
    await open(page, { ...PRICED, savedPct: 42.0, wouldRead: 7, insteadOf: 100 });
    await page.click('#chron-scan');
    await page.waitForTimeout(250);
    const txt = await page.textContent('#chron-body');
    expect(txt).toContain('42');
    expect(txt).toContain('7');
    expect(txt).not.toContain('97');
  });

  test('the real numbers render as a price with its units named', async ({ page }) => {
    await open(page, PRICED);
    await page.click('#chron-scan');
    await page.waitForTimeout(250);
    const txt = (await page.textContent('#chron-body')) || '';
    expect(txt).toContain('97.2');
    expect(txt).toContain('11');
    expect(txt).toContain('394');
    expect(txt).toMatch(/AI calls it/);           // 11 is calls, not items found
    expect(txt).toMatch(/frames across/);         // 394 is frames, not a tally
    expect(txt).not.toMatch(/found|grail|tallied/i);   // ★ never reads as a result
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
