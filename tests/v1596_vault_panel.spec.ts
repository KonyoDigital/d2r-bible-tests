import { test, expect } from './_net_stub';
import * as fs from 'fs';
import * as path from 'path';

// v1596 — 🏦 THE VAULT ACCUMULATOR PANEL, and the console's default tab.
//
// The engine shipped in v1578 and its board-side write in v1595. Four routes were live —
// /api/vault_scan, /api/vault_sweep, /api/vault_apply, /api/vault_forget — and NOT ONE had a
// control in the console. Plumbing with no tap: the v1576 defect class. This suite exists so the
// tap cannot quietly go missing again, and so the three lanes keep meaning three different things.
//
// THE LANE THAT MATTERS MOST IS THE ONE WITH NO BUTTON. `throwOut` is a suggestion held to a
// stricter bar than keep, and there is no un-throw in Diablo. The moment it gains a control — or
// starts being counted into the apply — the panel has become able to destroy his stash.

const ORIGIN = 'http://tvd.console.test';
const UI_HTML = fs.readFileSync(path.resolve(__dirname, '..', 'tv', 'control_ui.html'), 'utf8');

const PRICED = {
  ok: true,
  totals: { sessionsSeen: 3, framesSeen: 210, classified: 9, pagesRead: 12, skipped: 1 },
  savedPct: 90.0, wouldRead: 21, wouldClassify: 9, wouldReadPages: 12,
  upperBound: true, boundWhy: 'prices every candidate run as a readable ownership surface',
  insteadOf: 210, spent: 0, reels: ['reel_s1', 'reel_s2'], frames: [],
};

const SWEPT = {
  running: false, phase: 'done', reelsDone: 3, reelsTotal: 3,
  result: {
    ok: true, why: 'grounded 2 items', sessionsRead: ['s1', 's2'],
    owned: [
      { name: 'Ral Rune', lane: 'stash', kind: 'rune', count: 9, conf: 0.91, witnesses: [1, 2] },
      { name: 'Ist Rune', lane: 'stash', kind: 'rune', count: 2, conf: 0.77, witnesses: [1, 2] },
    ],
    unsure: [{ name: 'Vex Rune', why: 'only 1 independent witness (cross-frame) — needs 2' }],
    throwOut: [{ name: 'Chipped Topaz', lane: 'stash', why: 'the reader flagged it as junk',
                 conf: 0.93, witnesses: [1, 2, 3], suggestion: true }],
    held: [{ name: null, why: 'a 4-frame run in s2 was BLANK all the way through' }],
    totals: { sessionsSeen: 3, framesSeen: 210, classified: 9, pagesRead: 12, skipped: 1 },
  },
};

async function open(page: any, opts: any = {}) {
  const errs: string[] = [];
  page.on('pageerror', (e: any) => errs.push(String(e && e.message ? e.message : e)));
  await page.route(ORIGIN + '/ui', (r: any) =>
    r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: UI_HTML }));
  await page.route((u: URL) => u.pathname === '/api/vault_scan', (r: any) =>
    r.fulfill({ status: 200, contentType: 'application/json',
                body: JSON.stringify(opts.scan || PRICED) }));
  await page.route((u: URL) => u.pathname === '/api/vault_sweep', (r: any) =>
    r.fulfill({ status: 200, contentType: 'application/json',
                body: JSON.stringify(opts.sweep || { running: false, phase: 'idle', result: null }) }));
  await page.route((u: URL) => u.pathname === '/api/vault_apply', (r: any) =>
    r.fulfill({ status: 200, contentType: 'application/json',
                body: JSON.stringify(opts.apply || { ok: true, applied: {
                  ok: true, raised: ['Ral Rune', 'Ist Rune'], held: [], grail: [],
                  suggestions: 1, skipped: [] } }) }));
  // everything else on the console goes silent rather than hanging the page
  await page.route((u: URL) => u.pathname.startsWith('/api/') && !u.pathname.includes('vault'),
    (r: any) => r.abort());
  await page.goto(ORIGIN + '/ui', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(500);
  return errs;
}

test.describe('v1596 — the vault accumulator gets a tap, and the throw-out lane never gets a button', () => {
  test('★ the panel EXISTS and lives in THE RECORD zone with the rest of the sweeps', async ({ page }) => {
    await open(page);
    const home = await page.evaluate(() => {
      const el = document.getElementById('hd-vault');
      return { exists: !!el, banner: el?.closest('section.zone')?.querySelector('.zone-banner')?.textContent || '' };
    });
    expect(home.exists, 'four live routes had no control at all before v1596').toBe(true);
    expect(home.banner).toContain('THE RECORD');
  });

  test('★ every button is wired — a dead control teaches him to stop pressing', async ({ page }) => {
    await open(page);
    const wired = await page.evaluate(() => ({
      scan: typeof (window as any)._vaultScan === 'function',
      run: typeof (window as any)._vaultRun === 'function',
      apply: typeof (window as any)._vaultApply === 'function',
      forget: typeof (window as any)._vaultForget === 'function',
      poll: typeof (window as any)._vaultPollOnce === 'function',
      buttons: ['vault-scan', 'vault-run', 'vault-apply', 'vault-forget']
        .filter((id) => !!document.getElementById(id)).length,
    }));
    expect(wired).toMatchObject({ scan: true, run: true, apply: true, forget: true, poll: true });
    expect(wired.buttons).toBe(4);
  });

  test('pricing shows the ceiling and both lanes, and promises it spent nothing', async ({ page }) => {
    await open(page);
    await page.click('#vault-scan');
    await page.waitForTimeout(300);
    const txt = (await page.textContent('#vault-body')) || '';
    expect(txt).toContain('21');                    // the honest total, both lanes
    expect(txt).toMatch(/≤|at most/);               // stated as a bound, never a flat bill
    expect(txt).toContain('9');                     // classify lane
    expect(txt).toContain('12');                    // the READ lane
    expect(await page.textContent('#vault-note')).toMatch(/0 calls spent/);
  });

  test('★ the three lanes render as THREE different claims', async ({ page }) => {
    await open(page, { sweep: SWEPT });
    await page.waitForTimeout(400);
    const txt = (await page.textContent('#vault-review')) || '';
    expect(txt).toMatch(/OWNED/);
    expect(txt).toMatch(/UNSURE/);
    expect(txt).toMatch(/THROW-OUT/);
    expect(txt).toContain('Ral Rune');
    expect(txt).toContain('Vex Rune');
    expect(txt).toContain('Chipped Topaz');
    // unsure must say it is NOT owned — a name in a list reads as a claim unless something says otherwise
    expect(txt).toMatch(/not owned/i);
  });

  test('★★ THE THROW-OUT LANE HAS NO CONTROL OF ANY KIND', async ({ page }) => {
    await open(page, { sweep: SWEPT });
    await page.waitForTimeout(400);
    const lane = await page.evaluate(() => {
      const col = Array.from(document.querySelectorAll('#vault-review .chron-c'))
        .find((c) => /THROW-OUT/.test(c.textContent || ''));
      if (!col) return null;
      return {
        buttons: col.querySelectorAll('button').length,
        inputs: col.querySelectorAll('input,select,textarea').length,
        clickable: col.querySelectorAll('[onclick],[role="button"],[tabindex]').length,
        says: col.textContent || '',
      };
    });
    expect(lane, 'the throw-out lane must render').toBeTruthy();
    expect(lane!.buttons, 'a throw-out must never be actionable from here').toBe(0);
    expect(lane!.inputs, 'nor selectable — selection is the first half of a button').toBe(0);
    expect(lane!.clickable, 'nor clickable by any other affordance').toBe(0);
    expect(lane!.says, 'and it must say that it is only a suggestion').toMatch(/suggestion/i);
  });

  test('★ apply offers ONLY what cleared the gate', async ({ page }) => {
    await open(page, { sweep: SWEPT });
    await page.waitForTimeout(400);
    const btn = await page.evaluate(() => {
      const b = document.getElementById('vault-apply') as HTMLButtonElement | null;
      return { hidden: !!b?.hidden, text: b?.textContent || '' };
    });
    expect(btn.hidden).toBe(false);
    // 2 owned — NOT 4. unsure and throwOut must not be counted into the offer.
    expect(btn.text).toContain('2');
  });

  test('★ a sweep with NOTHING owned offers no write at all', async ({ page }) => {
    const onlySuggestions = { ...SWEPT, result: { ...SWEPT.result, owned: [] } };
    await open(page, { sweep: onlySuggestions });
    await page.waitForTimeout(400);
    const hidden = await page.evaluate(() =>
      !!(document.getElementById('vault-apply') as HTMLButtonElement | null)?.hidden);
    expect(hidden, 'unsure + throw-outs alone can only ever destroy — there is nothing to register')
      .toBe(true);
  });

  test('★ the apply receipt counts what did NOT go in, not only the wins', async ({ page }) => {
    await open(page, { sweep: SWEPT, apply: { ok: true, applied: {
      ok: true, raised: ['Ral Rune'], held: ['Ist Rune'], grail: [], suggestions: 1,
      skipped: ['Ohm Rune'] } } });
    await page.waitForTimeout(400);
    await page.click('#vault-apply');
    await page.waitForTimeout(300);
    const note = (await page.textContent('#vault-note')) || '';
    expect(note).toContain('1');
    expect(note, 'a merge-max hold is a row that did not go in — say so').toMatch(/already|held|kept/i);
    expect(note, 'an unreadable count is a row that did not go in — say so').toMatch(/skipped/i);
    expect(note, 'and the throw-outs must be named as NOT applied').toMatch(/NOT applied/i);
  });

  test('★ a refused apply never reads as a quiet success', async ({ page }) => {
    await open(page, { sweep: SWEPT, apply: { ok: false, why: 'the board window is not open' } });
    await page.waitForTimeout(400);
    await page.click('#vault-apply');
    await page.waitForTimeout(300);
    const note = (await page.textContent('#vault-note')) || '';
    expect(note).toMatch(/not registered/i);
    expect(note).toContain('board window is not open');
    const rearmed = await page.evaluate(() =>
      !(document.getElementById('vault-apply') as HTMLButtonElement | null)?.disabled);
    expect(rearmed, 'he must never be left with a dead button after a failure').toBe(true);
  });

  test('★★ NO "[object Object]" ANYWHERE — the bug a DOM assertion cannot see', async ({ page }) => {
    /* The first build of _vaultNames read `(r.name || r)`, so a held row of {name:null, why:...}
       fell back to the object and rendered "[object Object]". Every structural assertion passed:
       the lane existed, the count was right, the text was non-empty. Only a screenshot showed it.
       This test is the cheap permanent version of that look. */
    await open(page, { sweep: SWEPT });
    await page.waitForTimeout(400);
    const txt = (await page.textContent('#vault-review')) || '';
    expect(txt, 'a row with a null name is a REASON, not an item — it must never stringify the row')
      .not.toContain('[object Object]');
    expect(txt).not.toContain('undefined');
    expect(txt, 'and the refusal still has to say what it was').toContain('BLANK all the way through');
  });

  test('★ the panel loads without throwing — no dead seam in the new block', async ({ page }) => {
    const errs = await open(page, { sweep: SWEPT });
    await page.waitForTimeout(400);
    expect(errs, 'a throw here kills every later handler in the same script block').toEqual([]);
  });
});

test.describe('v1596 — SESSIONS is the console homepage', () => {
  test('★ the console opens on Sessions, not the TV·D cockpit', async ({ page }) => {
    await open(page);
    await page.waitForTimeout(600);
    const view = await page.evaluate(() => ({
      dataView: document.body.getAttribute('data-view'),
      lit: (document.querySelector('#head-tabs .ht.shell-on') as HTMLElement | null)?.dataset.tab || '',
    }));
    expect(view.dataView, 'Sessions is where the hunt is — it is what he opens the app to see')
      .toBe('sessions');
    expect(view.lit, 'and the tab has to LOOK selected, or the nav lies about where he is')
      .toBe('session');
  });

  test('TV·D is still reachable — making Sessions the default must not strand the cockpit', async ({ page }) => {
    await open(page);
    await page.waitForTimeout(500);
    await page.click('#head-tabs .ht[data-tab="tvd"]');
    await page.waitForTimeout(400);
    expect(await page.evaluate(() => document.body.getAttribute('data-view'))).toBe(null);
  });
});
