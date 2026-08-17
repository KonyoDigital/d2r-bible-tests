// v1754 — through the shared net stub: this spec asserts `expect(errors).toEqual([])`, and a
// console error array collects RESOURCE 404s as well as JS faults. bible.html pulls its
// typeface from fonts.googleapis.com, so on a runner with slow or blocked outbound network
// the spec goes red on the weather rather than on the code. The fixture fulfils fonts with an
// empty stylesheet (never aborts — an abort is itself a failed request).
import { test, expect } from './_net_stub';
import * as path from 'path';

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');

// v65 — Grail tracker made portable + richer. Two additions, both pure round-trips of
// data the app already owns (zero fabricated odds/categories):
//   1. Grail Progress tier breakdown — splits the single overall % into its honest
//      sub-pools (uber/elite vs grail uniques) counting only the user's ✓-owned items
//      per existing item.tier.
//   2. Backup & Share — export ALL saved localStorage state to portable JSON (copy /
//      download), and restore it (paste / .json upload) so a grail is never lost to a
//      cleared browser and can sync across devices. This spec locks both.
test.describe('v65 grail tier breakdown + backup/restore', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.evaluate(() => { (window as any).uiConfirm = () => Promise.resolve(true); }).catch(() => {});
    await page.waitForTimeout(1200);
  });

  test('tier breakdown renders and tracks owned-per-tier (sums match the overall grail count)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const allGrails = (ITEMS as any[]).filter((i) => i.tier === 'grail' || i.tier === 'uber');
      // re-query live each call — renderGrailTierBreakdown replaces the nodes via innerHTML
      const liveRows = () => [...document.querySelectorAll('#gp-tier-breakdown .gp-tier')];
      const num = (label: RegExp) => {
        const row = liveRows().find((x) => label.test(x.textContent || ''));
        return row ? (row.querySelector('.gp-tier-num') as HTMLElement).textContent!.trim() : null;
      };
      const parse = (s: string | null) => s ? s.split('/').map((x) => parseInt(x.trim(), 10)) : [NaN, NaN];
      const [gHaveBefore] = parse(num(/Grail uniques/));
      // mark a not-yet-owned grail-tier item, re-read, then revert
      const it = (ITEMS as any[]).find((i) => i.tier === 'grail' && !owned.has(i.n));
      (window as any).toggleOwned(it.n);
      const [gHaveAfter] = parse(num(/Grail uniques/));
      (window as any).toggleOwned(it.n);
      // totals across the rendered tier rows must reconstruct the whole grail pool
      const sumTotals = liveRows().map((x) => parse((x.querySelector('.gp-tier-num') as HTMLElement).textContent!.trim())[1]).reduce((a, b) => a + b, 0);
      return { rowCount: liveRows().length, gHaveBefore, gHaveAfter, sumTotals, poolLen: allGrails.length };
    });
    expect(r.rowCount).toBeGreaterThanOrEqual(1);
    expect(r.gHaveAfter).toBe(r.gHaveBefore + 1);   // owning one grail bumps the grail row
    expect(r.sumTotals).toBe(r.poolLen);            // the tier rows partition the whole pool
  });

  test('export builds a valid portable snapshot of the user\'s own state', async ({ page }) => {
    const r = await page.evaluate(() => {
      const it = (ITEMS as any[]).find((i) => (i.tier === 'grail' || i.tier === 'uber') && !owned.has(i.n));
      (window as any).toggleOwned(it.n);
      (window as any).exportProgress();
      const ta = document.getElementById('backup-textarea') as HTMLTextAreaElement;
      let parsed: any = null, ok = false;
      try { parsed = JSON.parse(ta.value); ok = true; } catch (e) {}
      const ownedInSnap = ok ? Object.keys(JSON.parse(parsed.data['d2r_foundLog'] || '{}')) : [];   // v677 — grail lives in the ledger
      (window as any).toggleOwned(it.n);   // revert
      return {
        ok,
        app: parsed && parsed.app,
        hasData: !!(parsed && parsed.data && typeof parsed.data === 'object'),
        includesItem: ownedInSnap.includes(it.n),
        fns: ['exportProgress', 'importProgress', 'copyProgress', 'downloadProgress', 'loadProgressFile']
          .map((n) => typeof (window as any)[n]),
      };
    });
    expect(r.ok).toBe(true);
    expect(r.app).toBe('d2r-bible');
    expect(r.hasData).toBe(true);
    expect(r.includesItem).toBe(true);                 // snapshot reflects live owned state
    expect(r.fns.every((t) => t === 'function')).toBe(true);
  });

  test('restore from a snapshot overwrites localStorage and survives reload', async ({ page }) => {
    page.on('dialog', (d) => d.accept());            // accept the overwrite confirm
    const target = await page.evaluate(() =>
      (ITEMS as any[]).find((i) => (i.tier === 'grail' || i.tier === 'uber') && !owned.has(i.n)).n);
    await page.evaluate((name) => {
      const snap = JSON.stringify({ app: 'd2r-bible', kind: 'grail-progress', version: 1, data: { d2r_foundLog: JSON.stringify({ [name]: 'restored' }) } });   // v677
      const ta = document.getElementById('backup-textarea') as HTMLTextAreaElement;
      ta.value = snap;
      (window as any).importProgress();
    }, target);
    await page.waitForTimeout(1400);                  // restore reloads at +600ms
    const owns = await page.evaluate((name) =>
      !!JSON.parse(localStorage.getItem('d2r_foundLog') || '{}')[name], target);   // v677
    expect(owns).toBe(true);                           // a real grail item -> survives the boot sanitizer
  });

  test('bad snapshot is rejected gracefully (no throw, error status shown)', async ({ page }) => {
    const r = await page.evaluate(() => {
      const ta = document.getElementById('backup-textarea') as HTMLTextAreaElement;
      ta.value = 'this is not json {{{';
      (window as any).importProgress();               // must not throw, must not reload
      const status = (document.getElementById('backup-status') as HTMLElement).textContent || '';
      return { status, stillOwnedKey: localStorage.getItem('d2r_owned') };
    });
    expect(r.status.toLowerCase()).toMatch(/valid|snapshot/);
  });

  test('no console errors on load or across the backup flow', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    await page.goto(URL);
    await page.evaluate(() => { (window as any).uiConfirm = () => Promise.resolve(true); }).catch(() => {});
    await page.waitForTimeout(1200);
    await page.evaluate(() => { (window as any).exportProgress(); });
    await page.waitForTimeout(150);
    expect(errors).toEqual([]);
  });
});
