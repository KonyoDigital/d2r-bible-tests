import { test, expect } from './_net_stub';
import * as path from 'path';

// v2219 — "the shadow dancers are still here.. i ticked it off"
//
// Twice in one morning he reported an inbox row for something already answered. BOTH TIMES THE
// STORE WAS CORRECT: the queue was empty and both names sat in d2r_foundLog with real dates. What
// he was looking at was a snapshot from before, and his own footer said so — "2 NEED YOU (DISK
// READ 10 MIN AGO)".
//
// MEASURED: every renderInbox() call in bible.html hangs off a CLICK — the card header and the two
// action paths. Nothing repainted on focus, on visibility, or on a timer. So a change arriving from
// anywhere else (a sweep applying, a restore, a tick in another tab, the console writing through
// the bridge) left the old rows on screen indefinitely — and every one looked like a stuck item.
//
// ⚠ THE FIX IS THE ORDERING, NOT THE REPAINT. kaiChronicleSync is what drops a row whose name has
// become settled; repainting without it faithfully redraws the same stale queue. The render was
// never the broken half.

const URL = 'file://' + path.resolve(__dirname, '..', 'bible.html');
const NAME = 'Shadow Dancer';

test.describe('v2219 the inbox repaints when the ledger moves', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(URL);
    await page.waitForTimeout(300);
    await page.evaluate((n: string) => {
      localStorage.setItem('d2r_ownerClaim', '*');
      localStorage.setItem('d2r_chronicleInbox', JSON.stringify([{
        name: n, firstSeenTs: 0, frameId: null, tier: 'grail', sessionId: null,
        source: 'chronicle-sweep', proposedAt: 1, gateHeld: true,
        gateWhy: 'only 1 independent witness' }]));
      localStorage.setItem('d2r_chronicleInboxLog', '[]');
    }, NAME);
    await page.reload();
    await page.waitForTimeout(1500);
  });

  const queue = (page: any) => page.evaluate(() =>
    (JSON.parse(localStorage.getItem('d2r_chronicleInbox') || '[]') || []).map((x: any) => x && x.name));

  test('a row settled from ELSEWHERE leaves the queue on the next refresh', async ({ page }) => {
    expect(await queue(page), 'the fixture did not reach the queue').toContain(NAME);

    // the ledger changes WITHOUT touching the inbox — exactly what my restore did to his board
    await page.evaluate((n: string) => {
      const fl = JSON.parse(localStorage.getItem('d2r_foundLog') || '{}');
      fl[n] = 'Aug 27, 2026 · 11:44';
      localStorage.setItem('d2r_foundLog', JSON.stringify(fl));
    }, NAME);
    expect(await queue(page), 'writing the ledger must not clear the queue by itself — that would '
      + 'mean something other than the sync is mutating it').toContain(NAME);

    const why = await page.evaluate(() => (window as any)._inboxRefresh('test'));
    expect(why, '_inboxRefresh is gone — the panel is back to repainting only on a click').toBe('test');
    expect(await queue(page),
      `"${NAME}" is in the found ledger and still sitting in his inbox. This is the row he reported `
      + `twice as "i ticked it off" — the data was right and the panel was showing a snapshot.`)
      .not.toContain(NAME);
  });

  test('it SYNCS before it paints, or it just redraws the stale queue', async ({ page }) => {
    const order: string[] = await page.evaluate(() => {
      const seen: string[] = [];
      const W = window as any;
      const sync = W.kaiChronicleSync, paint = W.renderInbox;
      W.kaiChronicleSync = function () { seen.push('sync'); return sync.apply(this, arguments); };
      W.renderInbox = function () { seen.push('paint'); return paint.apply(this, arguments); };
      W._inboxRefresh('order');
      W.kaiChronicleSync = sync; W.renderInbox = paint;
      return seen;
    });
    expect(order.indexOf('sync'), 'the sync never ran').toBeGreaterThanOrEqual(0);
    expect(order.indexOf('paint'), 'the paint never ran').toBeGreaterThanOrEqual(0);
    expect(order.indexOf('sync')).toBeLessThan(order.indexOf('paint'));
  });

  test('it is wired to visibility and focus, not only to a timer', async ({ page }) => {
    // a 45s timer alone would still leave a stale panel in front of him for most of a minute
    // every time he tabs back
    const src = await page.evaluate(() => document.documentElement.innerHTML);
    expect(src).toContain("visibilitychange");
    expect(src).toContain("_inboxRefresh('visible')");
    expect(src).toContain("_inboxRefresh('focus')");
  });

  test('it does nothing while the tab is hidden, and never re-enters', async ({ page }) => {
    // ⚠ a panel that costs him frames while he plays would be a worse defect than the one it fixes
    const r = await page.evaluate(() => {
      const W = window as any;
      Object.defineProperty(document, 'hidden', { value: true, configurable: true });
      const hiddenResult = W._inboxRefresh('while-hidden');
      Object.defineProperty(document, 'hidden', { value: false, configurable: true });
      // re-entrancy: a sync that itself triggers a refresh must not recurse
      let depth = 0, max = 0;
      const sync = W.kaiChronicleSync;
      W.kaiChronicleSync = function () {
        depth++; max = Math.max(max, depth);
        W._inboxRefresh('reentrant');
        depth--;
        return sync.apply(this, arguments);
      };
      W._inboxRefresh('outer');
      W.kaiChronicleSync = sync;
      return { hiddenResult, max };
    });
    expect(r.hiddenResult, 'the refresh ran while the tab was hidden — it would burn cycles behind '
      + 'the game for nothing').toBeUndefined();
    expect(r.max, 're-entered: a refresh triggered from inside the sync recursed').toBe(1);
  });
});
