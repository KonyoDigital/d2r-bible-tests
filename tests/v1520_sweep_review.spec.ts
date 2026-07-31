import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1520 — THE PROPOSAL REVIEW: the surface Konyo actually decides from.
//
// The rule this spec exists to hold: never a count without the evidence behind it. Every name the
// sweep would add carries the gate's own sentence and its witnesses; every held name carries the
// reason it was held. A review that showed "12 would be added" and nothing else would be asking him
// to trust the number, which is the one thing this whole arc is built not to do.

const ORIGIN = 'http://tvd.console.test';
const UI_HTML = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

const DONE = {
  running: false, phase: 'done', reelsDone: 3, reelsTotal: 3, classified: 11, pagesRead: 4,
  error: null, lanes: ['claude', 'grok'],
  result: {
    totals: { reels: 3, framesSeen: 394, classified: 11, pagesRead: 4 },
    lanes: ['claude', 'grok'],
    wouldAdd: {
      uniques: [
        { name: 'Harlequin Crest', why: 'corroborated by cross-frame, cross-lane',
          witnesses: ['cross-frame', 'cross-lane'],
          seen: [{ reel: 's_100', frame: 'f2.jpg', lane: 'claude' },
                 { reel: 's_100', frame: 'f2.jpg', lane: 'grok' }] },
        { name: 'Windforce', why: 'corroborated by cross-reel-3+, printed',
          witnesses: ['cross-reel-3+', 'printed'] },
      ],
      sets: [{ name: "Tal Rasha's Howling Wind", why: 'corroborated by cross-lane, printed',
               witnesses: ['cross-lane', 'printed'] }],
    },
    held: [{ ledger: 'uniques', name: 'Stormshield',
             why: 'only 1 independent witness (printed) — needs 2', sightings: 1,
             seen: [{ reel: 's_200', frame: 'f7.jpg', lane: 'claude' }] }],
    refused: [{ reel: 's_100', frame: 'f2.jpg', why: 'no-found-state' }],
    setGroups: {},
  },
};

async function open(page: any, sweepState: any, visits: any[] = []) {
  await page.route((u: URL) => u.pathname === '/api/chronicle_visits', (r: any) =>
    r.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ ok: true, visits, spent: 0 }) }));
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI_HTML }));
  // url predicates, not globs: a '**/api/**' catch-all wins the match and aborts the call under test
  await page.route((u: URL) => u.pathname.startsWith('/api/') && !u.pathname.includes('chronicle'),
    (r: any) => r.abort());
  await page.route((u: URL) => u.pathname === '/api/chronicle_sweep', (r: any) =>
    r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(sweepState) }));
  await page.route((u: URL) => u.pathname === '/api/chronicle_scan', (r: any) =>
    r.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ ok: true, totals: { reels: 3, framesSeen: 394, classified: 11 },
                             savedPct: 97.2, wouldRead: 11, insteadOf: 394, reels: [] }) }));
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(500);
}

test.describe('v1520 — the review he decides from', () => {
  test('a finished sweep paints itself on load — a refresh never hides work in flight', async ({ page }) => {
    await open(page, DONE);
    expect(await page.isHidden('#chron-review')).toBe(false);
  });

  test('★ every grounded name carries the gate’s own sentence', async ({ page }) => {
    await open(page, DONE);
    const rows = await page.$$eval('.chron-c.add .chron-n', (n: any[]) =>
      n.map((x) => ({ name: x.querySelector('b')?.textContent, why: x.querySelector('i')?.textContent })));
    expect(rows).toHaveLength(3);
    for (const r of rows) {
      expect(r.name).toBeTruthy();
      expect(r.why, `${r.name} was grounded with no reason — not reviewable`).toMatch(/corroborated by/);
    }
  });

  test('★ every HELD name carries the reason it was held', async ({ page }) => {
    await open(page, DONE);
    const held = await page.textContent('.chron-c.held');
    expect(held).toContain('Stormshield');
    expect(held).toContain('only 1 independent witness');
  });

  test('the two ledgers stay apart in the review too', async ({ page }) => {
    await open(page, DONE);
    const heads = await page.$$eval('.chron-c-h', (n: any[]) => n.map((x) => x.textContent));
    expect(heads[0]).toMatch(/Holy Grail \(2\)/);
    expect(heads[1]).toMatch(/Set pieces \(1\)/);
    // and a set piece never appears under the grail column
    const grail = await page.textContent('.chron-cols .chron-c:nth-child(1)');
    expect(grail).not.toContain('Tal Rasha');
  });

  test('★ WHICH EYES RAN is part of the answer', async ({ page }) => {
    // "claude only" and "both agreed" are different confidences and the gate scores them differently
    await open(page, DONE);
    expect(await page.textContent('.chron-run')).toMatch(/eyes:\s*claude \+ grok/);
  });

  test('the pages the reader REFUSED are counted in the open', async ({ page }) => {
    await open(page, DONE);
    expect(await page.textContent('.chron-run')).toMatch(/1.*refused/);
  });

  test('★ until an Apply exists, the panel says nothing was written', async ({ page }) => {
    await open(page, DONE);
    expect(await page.textContent('#chron-note')).toMatch(/nothing has been written/i);
  });

  test('a running sweep shows progress instead of an empty panel', async ({ page }) => {
    await open(page, { running: true, phase: 'reading', reelsDone: 1, reelsTotal: 3,
                       classified: 4, pagesRead: 2, error: null, lanes: ['claude'], result: null });
    const body = await page.textContent('#chron-body');
    expect(body).toMatch(/reel 1 of 3/);
    expect(body).toMatch(/4 frames classified/);
    expect(await page.isHidden('#chron-review')).toBe(true);
  });

  test('★ a refused START names the refusal instead of falling silent', async ({ page }) => {
    await open(page, { running: false, phase: 'idle', result: null, error: null, lanes: [] });
    await page.route((u: URL) => u.pathname === '/api/chronicle_sweep', (r: any) => {
      if (r.request().method() !== 'POST') return r.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ running: false, phase: 'idle', result: null, error: null, lanes: [] }) });
      return r.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ ok: false, why: 'the primary (Claude) lane is unavailable' }) });
    });
    await page.click('#chron-scan');            // reveals the real-run button
    await page.waitForTimeout(300);
    await page.click('#chron-run');
    await page.waitForTimeout(400);
    const body = await page.textContent('#chron-body');
    expect(body).toContain('cannot sweep');
    expect(body).toContain('Claude) lane is unavailable');
    expect(await page.isDisabled('#chron-run'), 'he must never be left stuck').toBe(false);
  });

  test('★ the real run is offered only after he has seen what it costs', async ({ page }) => {
    await open(page, { running: false, phase: 'idle', result: null, error: null, lanes: [] });
    expect(await page.isHidden('#chron-run')).toBe(true);
    await page.click('#chron-scan');
    await page.waitForTimeout(300);
    expect(await page.isHidden('#chron-run')).toBe(false);
  });

  // ── v1526 WHAT HE OPENED IN GAME ────────────────────────────────────────────────────────────
  test('the in-game visits show as a receipt of what he actually opened', async ({ page }) => {
    await open(page, DONE, [
      { ts: Date.now() - 6 * 60000, ledger: 'uniques', n: 14, label: '🏆 Holy Grail' },
      { ts: Date.now() - 3 * 3600000, ledger: '', n: 3, label: '📜 ledger unread' },
    ]);
    const rows = await page.$$eval('.chron-v', (n: any[]) => n.map((x) => x.textContent));
    expect(rows).toHaveLength(2);
    expect(rows[0]).toContain('Holy Grail');
    expect(rows[0]).toContain('14 frames');
    expect(rows[0], 'epoch ms must not be parsed as an ISO string').toContain('6m ago');
    expect(rows[1]).toContain('3h ago');
  });

  test('★ a visit whose ledger was never read is FLAGGED, not hidden', async ({ page }) => {
    // it is the one a sweep could mis-file, so it is the one he should see
    await open(page, DONE, [{ ts: Date.now(), ledger: '', n: 3, label: '📜 ledger unread' }]);
    expect(await page.locator('.chron-v.unread').count()).toBe(1);
  });

  test('no in-game visits means no strip at all — not an empty box', async ({ page }) => {
    await open(page, DONE, []);
    expect(await page.isHidden('#chron-visits')).toBe(true);
  });

  // ── v1525 THE EVIDENCE ──────────────────────────────────────────────────────────────────────
  test('★ every grounded name can show the FRAMES behind it', async ({ page }) => {
    // "why does it think I have Windforce" must be answerable with a frame he can look at
    await open(page, DONE);
    const row = page.locator('.chron-c.add .chron-n', { hasText: 'Harlequin Crest' });
    expect(await row.locator('.chron-ev').textContent()).toMatch(/2 frames/);
    await row.locator('summary').click();
    const frames = row.locator('.chron-fr');
    expect(await frames.count()).toBe(2);
    const src = await frames.first().getAttribute('href');
    expect(src, 'the link must point at the real archived still').toContain('/hist/reel_s_100/f2.jpg');
  });

  test('★ each frame names the LANE that saw it — who saw it is half the answer', async ({ page }) => {
    await open(page, DONE);
    const row = page.locator('.chron-c.add .chron-n', { hasText: 'Harlequin Crest' });
    await row.locator('summary').click();
    const lanes = await row.locator('.chron-fr-lane').allTextContents();
    expect(lanes).toEqual(['claude', 'grok']);
  });

  test('a HELD name carries its evidence too — that is the row he judges by hand', async ({ page }) => {
    await open(page, DONE);
    const row = page.locator('.chron-c.held .chron-n', { hasText: 'Stormshield' });
    await row.locator('summary').click();
    expect(await row.locator('.chron-fr').count()).toBe(1);
  });

  test('a name with no evidence shows no drawer rather than an empty one', async ({ page }) => {
    await open(page, DONE);
    const row = page.locator('.chron-c.add .chron-n', { hasText: 'Windforce' });
    expect(await row.locator('.chron-ev').count()).toBe(0);
  });

  test('★ a frame swept off disk says so instead of showing a broken box', async ({ page }) => {
    // hist is pruned by the retention governor; a proposal can outlive its own stills
    await open(page, DONE);
    const row = page.locator('.chron-c.add .chron-n', { hasText: 'Harlequin Crest' });
    await row.locator('summary').click();
    await page.waitForTimeout(400);
    expect(await row.locator('.chron-fr.gone').count()).toBeGreaterThan(0);
  });

  // ── v1523 REGISTER ──────────────────────────────────────────────────────────────────────────
  test('the register button appears only when something is GATED to write', async ({ page }) => {
    await open(page, { ...DONE, result: { ...DONE.result, wouldAdd: { uniques: [], sets: [] } } });
    expect(await page.isHidden('#chron-apply')).toBe(true);
    await open(page, DONE);
    expect(await page.isHidden('#chron-apply')).toBe(false);
    expect(await page.textContent('#chron-apply')).toContain('3');   // 2 uniques + 1 set piece
  });

  test('a successful register reports what landed AND what he already had', async ({ page }) => {
    await open(page, DONE);
    await page.route((u: URL) => u.pathname === '/api/chronicle_apply', (r: any) =>
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
        ok: true, applied: { uniques: ['Harlequin Crest', 'Windforce'],
                             sets: ["Tal Rasha's Howling Wind"], skipped: ['Stormshield'] } }) }));
    await page.click('#chron-apply');
    await page.waitForTimeout(400);
    const note = (await page.textContent('#chron-note')) || '';
    expect(note).toContain('3 registered');
    expect(note).toContain('1 you already had');
    expect(note).toMatch(/undo from the board/);
    expect(await page.isHidden('#chron-apply'), 'a done write should not invite a repeat').toBe(true);
  });

  test('★ a FAILED register never reads as a quiet success', async ({ page }) => {
    // the worst possible answer is silence: the proposal still looks unapplied and he runs it again
    await open(page, DONE);
    await page.route((u: URL) => u.pathname === '/api/chronicle_apply', (r: any) =>
      r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
        ok: false, why: 'the board window is not open' }) }));
    await page.click('#chron-apply');
    await page.waitForTimeout(400);
    const note = (await page.textContent('#chron-note')) || '';
    expect(note).toMatch(/not registered/);
    expect(note).toContain('board window is not open');
    expect(await page.isDisabled('#chron-apply')).toBe(false);
    expect(await page.isHidden('#chron-apply')).toBe(false);
  });

  test('an errored sweep says so, and does not present a stale result as fresh', async ({ page }) => {
    await open(page, { running: false, phase: 'error', error: 'grok CLI vanished',
                       result: null, lanes: ['claude'] });
    expect(await page.textContent('#chron-body')).toContain('grok CLI vanished');
  });
});
