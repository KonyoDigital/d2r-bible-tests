import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1550 — TWO TOOLS THAT EXISTED WITH NO TAP.
//
// An audit of every `path == "/api/…"` in control_app.py against control_ui.html found four routes
// with no consumer. Two belong to the `tvd` CLI. These two were nobody's:
//
//   /api/chronicle_gate   (v1531) re-gates the LAST sweep's evidence at different thresholds, free,
//     and NAMES what loosening would let in and tightening would keep out. CHRONICLE_ARC.md lists
//     tuning the gate as the #1 remaining job in the arc — and the tool for it had no button.
//   /api/chronicle_forget (v1524) clears the sweep memory. Its own docstring reads "an optimisation
//     he cannot clear is a cage", and it was one.
//
// Same shape as v1547's TZ panel: the plumbing was built, the tap never was.

const ORIGIN = 'http://tvd.console.test';
const UI_HTML = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

const GATE = {
  ok: true,
  current: { confFloor: 0.55, minWitnesses: 2, grounded: 7, held: 3 },
  asked: { confFloor: 0.35, minWitnesses: 1, grounded: 10, held: 0 },
  wouldGainNames: ['Windforce', 'Death’s Web', 'Griffon’s Eye'],
  wouldLoseNames: [],
};

const SWEEP_DONE = {
  running: false, phase: 'done',
  result: { totals: { reels: 2, framesSeen: 90, classified: 4, pagesRead: 2, uniques: 7, sets: 0 },
    reels: [], wouldAdd: { uniques: ['Windforce'], sets: [] }, held: [] },
};

async function open(page: any, opts: any = {}) {
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI_HTML }));
  await page.route((u: URL) => u.pathname.startsWith('/api/'), (r: any) => {
    const p = new URL(r.request().url()).pathname;
    if (p === '/api/chronicle_gate') {
      opts.onGate?.(new URL(r.request().url()));
      return r.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify(opts.gate ?? GATE) });
    }
    if (p === '/api/chronicle_forget') {
      opts.onForget?.(r.request().method());
      return r.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ ok: true, forgot: true }) });
    }
    if (p === '/api/chronicle_sweep' && opts.sweep) {
      return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(opts.sweep) });
    }
    return r.abort();
  });
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(700);
}

test.describe('v1550 — the gate tuner and the sweep memory get a button', () => {
  test('★ both controls EXIST in the console', async ({ page }) => {
    await open(page);
    expect(await page.locator('#chron-tune').count(), 'the gate tuner').toBe(1);
    expect(await page.locator('#chron-forget').count(), 'forget what is swept').toBe(1);
  });

  test('★ the tuner NAMES what would change, not just counts it', async ({ page }) => {
    // "3 more would ground" is unarguable. "Windforce would ground" can be checked against a frame.
    await open(page);
    await page.evaluate(() => { (document.getElementById('chron-tune') as any).hidden = false; });
    await page.click('#chron-tune');
    await page.waitForTimeout(500);
    const txt = (await page.textContent('#ct-out')) || '';
    expect(txt).toContain('would let IN');
    expect(txt).toContain('Windforce');
    expect(txt).toContain('7');            // grounded now
    expect(txt).toContain('10');           // grounded at the asked thresholds
  });

  test('★ it says it re-gates rather than re-reads — the reason it is free', async ({ page }) => {
    await open(page);
    await page.evaluate(() => { (document.getElementById('chron-tune') as any).hidden = false; });
    await page.click('#chron-tune');
    await page.waitForTimeout(500);
    const txt = (await page.textContent('#ct-out')) || '';
    expect(txt).toContain('no frame is read again');
    expect(txt).toContain('nothing is written');
  });

  test('moving a slider re-asks with the new thresholds', async ({ page }) => {
    const asked: string[] = [];
    await open(page, { onGate: (u: URL) => asked.push(u.search) });
    await page.evaluate(() => { (document.getElementById('chron-tune') as any).hidden = false; });
    await page.click('#chron-tune');
    await page.waitForTimeout(400);
    await page.fill('#ct-floor', '0.35').catch(() => {});
    await page.evaluate(() => {
      const el = document.getElementById('ct-floor') as HTMLInputElement;
      el.value = '0.35'; el.dispatchEvent(new Event('input'));
    });
    await page.waitForTimeout(400);
    expect(asked.some((s) => s.includes('floor=0.35')), 'asked: ' + JSON.stringify(asked)).toBe(true);
  });

  test('★ nothing to re-gate says so, instead of an empty panel', async ({ page }) => {
    await open(page, { gate: { ok: false, why: 'no sweep evidence in memory — run a sweep first' } });
    await page.evaluate(() => { (document.getElementById('chron-tune') as any).hidden = false; });
    await page.click('#chron-tune');
    await page.waitForTimeout(500);
    expect((await page.textContent('#ct-out')) || '').toContain('no sweep evidence in memory');
  });

  test('★ the tuner is HIDDEN until there is a sweep to tune', async ({ page }) => {
    // a control that can only answer "nothing to do" teaches him to stop pressing things
    await open(page);
    expect(await page.isHidden('#chron-tune')).toBe(true);
  });

  test('★ FORGET needs a second tap, and says what it costs', async ({ page }) => {
    let hits = 0;
    await open(page, { onForget: () => { hits += 1; } });
    await page.click('#chron-forget');
    await page.waitForTimeout(200);
    expect(hits, 'the first tap must ARM, never fire').toBe(0);
    expect((await page.textContent('#chron-forget')) || '').toContain('re-reads every reel');
    await page.click('#chron-forget');
    await page.waitForTimeout(400);
    expect(hits, 'the second tap fires it').toBe(1);
    expect((await page.textContent('#chron-forget')) || '').toContain('forgotten');
  });

  test('forget uses POST — the route only answers POST', async ({ page }) => {
    const methods: string[] = [];
    await open(page, { onForget: (m: string) => methods.push(m) });
    await page.click('#chron-forget');
    await page.waitForTimeout(150);
    await page.click('#chron-forget');
    await page.waitForTimeout(400);
    expect(methods).toEqual(['POST']);
  });

  test('★ every /api route in the console now has a consumer, or a named owner', async ({ page }) => {
    // the audit that found these two, kept as a test so the next orphan surfaces on its own
    const app = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_app.py'), 'utf8');
    const ui = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');
    let tvd = '';
    try { tvd = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'tvd'), 'utf8'); } catch { /* */ }
    const routes = [...new Set([...app.matchAll(/path == "(\/api\/[a-z_0-9]+)"/g)].map((m) => m[1]))];
    const orphans = routes.filter((r) => !ui.includes(r) && !tvd.includes(r));
    expect(orphans, 'a route with no caller is plumbing with no tap — give it one or delete it')
      .toEqual([]);
    expect(routes.length).toBeGreaterThan(25);
  });

  test('★ v1551 — the PRICE pass names the frames and the verdict, like the CLI does', async ({ page }) => {
    // "11 classifies" reads as "11 Chronicle pages". It means "11 screens worth looking at", and on
    // his footage every one was a lobby, a stash or a blank capture. The CLI has printed both since
    // v1541; the console — the only surface his Windows PC will ever show him — printed neither.
    await page.route(ORIGIN + '/ui', (r: any) =>
      r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI_HTML }));
    await page.route((u: URL) => u.pathname.startsWith('/api/'), (r: any) => {
      const p = new URL(r.request().url()).pathname;
      if (p !== '/api/chronicle_scan') return r.abort();
      return r.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({
        ok: true, reels: [{ reel: 'reel_s_1', runs: 6, classified: 4 }],
        totals: { reels: 1, framesSeen: 153, classified: 4, blankRuns: 1 },
        savedPct: 97.4, wouldRead: 4, insteadOf: 153, spent: 0,
        frames: ['reel_s_1/f_100.jpg', 'reel_s_1/f_200.jpg'],
        verdict: { state: 'no-chronicle', ok: true,
          say: '4 still screen(s) across 1 reel(s) were examined and NONE was a Chronicle page — so there was nothing to read. This is not a reader failure.',
          do: 'Open the Chronicle in game while TV DIABLO is watching.' },
      }) });
    });
    await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(500);
    await page.click('#chron-scan');
    await page.waitForTimeout(700);
    const txt = (await page.textContent('#chron-body')) || '';
    expect(txt, 'the verdict travels with the price').toContain('NONE was a Chronicle page');
    expect(txt, 'and what to do about it').toContain('Open the Chronicle in game');
    expect(txt, 'and the frames he can open himself').toContain('f_100.jpg');
    expect(await page.locator('.chron-frames').count()).toBe(1);
    expect((await page.textContent('#chron-note')) || '',
      'the free pass must still say it spent nothing').toContain('0 calls spent');
  });
});
